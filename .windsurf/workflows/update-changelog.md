---
description: Update changelog with recent changes
---

# Update Changelog Workflow

This workflow helps update the changelog.md file with recent changes across all branches since the last changelog update.

## Steps

### 1. Check Current Changelog Status
```bash
# Check if changelog.md exists and get last update date
if [ -f "changelog.md" ]; then
    echo "changelog.md found"
    git log -1 --format="%h %s" changelog.md
else
    echo "changelog.md not found"
fi
```

### 2. Get Last Changelog Update
```bash
# Find the most recent commit that modified changelog.md
LAST_CHANGELOG_COMMIT=$(git log -1 --format="%H" changelog.md 2>/dev/null || echo "")
echo "Last changelog commit: $LAST_CHANGELOG_COMMIT"
```

### 3. Get All Branches
```bash
# List all branches
git branch -a
```

### 4. Check Major Changes Since Last Changelog Update
```bash
# Get commits since last changelog update across all branches

if [ -n "$LAST_CHANGELOG_COMMIT" ]; then
    echo "Changes since last changelog update:"
    git log --oneline --since="$LAST_CHANGELOG_COMMIT" --all
else
    echo "No previous changelog found, showing recent commits:"
    git log --oneline --since="1 month ago" --all
fi
```

### 5. Analyze File Changes
```bash
# Get most changed files since last changelog update

if [ -n "$LAST_CHANGELOG_COMMIT" ]; then
    echo "Most changed files since last changelog update:"
    git diff --name-only "$LAST_CHANGELOG_COMMIT" HEAD | sort | uniq -c | sort -nr | head -20
else
    echo "Recent file changes:"
    git diff --name-only HEAD~50 HEAD | sort | uniq -c | sort -nr | head -20
fi
```

### 6. Generate Changelog Summary
```bash
# Generate summary of major changes

echo "=== CHANGELOG SUMMARY ==="
echo "Date: $(date)"
echo ""

if [ -n "$LAST_CHANGELOG_COMMIT" ]; then
    echo "Changes since: $(git log -1 --format="%h %s" $LAST_CHANGELOG_COMMIT)"
    echo ""

    # Get commit messages and categorize
    echo "### Committed Changes:"
    git log --oneline --since="$LAST_CHANGELOG_COMMIT" --all | \
    grep -E "(feat|fix|refactor|BREAKING|docs|test)" | \
    head -20
else
    echo "### Recent Committed Changes (Last 30 Days):"
    git log --oneline --since="1 month ago" --all | \
    grep -E "(feat|fix|refactor|BREAKING|docs|test)" | \
    head -20
fi

# Check for uncommitted changes
echo ""
echo "### Uncommitted Changes:"
if git diff --quiet && git diff --cached --quiet; then
    echo "No uncommitted changes detected."
else
    echo "Uncommitted changes found:"
    git status --short
    echo ""
    echo "Uncommitted files:"
    git diff --name-only
    git diff --cached --name-only
fi
```

### 7. Update changelog.md
```bash
# Create or update changelog.md with summary

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "//' | sed 's/"//')

# Determine if version needs increment (patch version for typical updates)
if [[ "$CURRENT_VERSION" =~ ^[0-9]+\.[0-9]+\.([0-9]+)$ ]]; then
    CURRENT_PATCH=${BASH_REMATCH[1]}
    NEW_PATCH=$((CURRENT_PATCH + 1))
    NEW_VERSION="${CURRENT_VERSION%.*}.$NEW_PATCH"

    # Update pyproject.toml with new version
    sed -i.bak "s/^version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml

    echo "Updated version from $CURRENT_VERSION to $NEW_VERSION"
    VERSION_TO_USE=$NEW_VERSION
else
    VERSION_TO_USE=$CURRENT_VERSION
    echo "Using existing version: $VERSION_TO_USE"
fi

# Backup existing changelog
if [ -f "changelog.md" ]; then
    cp changelog.md changelog.md.backup
fi

# Create temporary file with new entry
cat > changelog_entry.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [VERSION_PLACEHOLDER] - $(date +%Y-%m-%d)

### Added
- [Add new features here based on git log analysis]

### Changed
- [List changes to existing functionality]

### Fixed
- [List bug fixes]

### Removed
- [List removed features]

### Refactored
- [List code refactoring improvements]

### Documentation
- [List documentation updates]

### Tests
- [List test improvements]

---

[Previous entries remain below this line]
EOF

# Replace version placeholder
sed -i "s/VERSION_PLACEHOLDER/$VERSION_TO_USE/" changelog_entry.md

# Remove empty sections (those with only placeholder text)
# Note: This sed command removes sections that only contain placeholder text.
# For manual control, you can edit the changelog_entry.md file directly
# and remove any sections that don't have actual content.
sed -i '/^### [A-Z].*$/,/^$/{
    /^### [A-Z].*$/!d
    /^\[.*\]$/!d
    /^---$/!d
    /^$/d
}' changelog_entry.md

# Merge with existing changelog if it exists
if [ -f "changelog.md.backup" ]; then
    tail -n +6 changelog.md.backup >> changelog_entry.md
fi

# Replace old changelog
mv changelog_entry.md changelog.md

echo "changelog.md updated with version $VERSION_TO_USE"
```

### 8. Review and Manual Commit
```bash
# Review the updated changelog
echo "Review updated changelog.md:"
cat changelog.md

echo ""
echo "Files that need to be committed manually:"
echo "- changelog.md"
if [ -f "pyproject.toml.bak" ]; then
    echo "- pyproject.toml (version was updated)"
fi

echo ""
echo "Manual commit command:"
echo "git add changelog.md"
if [ -f "pyproject.toml.bak" ]; then
    echo "git add pyproject.toml"
fi
echo "git commit -m \"docs: update changelog with version $VERSION_TO_USE\""

echo "Changelog update complete! Please commit manually."
```

## Usage

1. Run this workflow from the terminus_core_python directory
2. Review the generated changelog entries
3. Edit the changelog.md to add meaningful descriptions for each change
4. Commit the updated changelog

## Notes

- Focus on user-facing changes in the changelog
- Keep entries brief and to the point
- Use semantic versioning categories (Added, Changed, Fixed, etc.)
- Include breaking changes prominently
- Group related changes together
- This workflow analyzes both COMMITTED and UNCOMMITTED changes
- For committed changes, it uses git log to analyze commit messages
- For uncommitted changes, it uses git status and git diff to show modified files
- Manual editing of the changelog.md is still required to add meaningful descriptions
