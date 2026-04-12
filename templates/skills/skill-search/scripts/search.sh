#!/usr/bin/env bash
# Searches installed skills by keyword for dynamic skill discovery.
# Scans all SKILL.md files under .github/skills/ and returns matches where
# the keyword appears in the skill directory name or the YAML frontmatter
# description field.
#
# Usage: scripts/search.sh <keyword>

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: search.sh <keyword>" >&2
    exit 1
fi

KEYWORD="$1"
SKILLS_ROOT=".github/skills"

if [ ! -d "$SKILLS_ROOT" ]; then
    echo "Error: Skills directory not found: $SKILLS_ROOT" >&2
    exit 1
fi

KEYWORD_LOWER="$(echo "$KEYWORD" | tr '[:upper:]' '[:lower:]')"

FOUND=0
printf "%-28s %-65s %s\n" "SKILL" "DESCRIPTION" "PATH"
printf "%-28s %-65s %s\n" "-----" "-----------" "----"

for DIR in "$SKILLS_ROOT"/*/; do
    [ -d "$DIR" ] || continue
    SKILL_FILE="${DIR}SKILL.md"
    [ -f "$SKILL_FILE" ] || continue

    SKILL_NAME="$(basename "$DIR")"
    DESCRIPTION=""

    # Extract description from YAML frontmatter (first 10 lines)
    IN_FRONTMATTER=0
    while IFS= read -r LINE; do
        if echo "$LINE" | grep -qE '^---[[:space:]]*$'; then
            if [ "$IN_FRONTMATTER" -eq 1 ]; then
                break
            fi
            IN_FRONTMATTER=1
            continue
        fi
        if [ "$IN_FRONTMATTER" -eq 1 ]; then
            if echo "$LINE" | grep -qiE '^\s*description:'; then
                DESCRIPTION="$(echo "$LINE" | sed 's/^[[:space:]]*description:[[:space:]]*"*//;s/"*[[:space:]]*$//')"
                break
            fi
        fi
    done < <(head -10 "$SKILL_FILE")

    # Match keyword against skill name or description (case-insensitive)
    NAME_LOWER="$(echo "$SKILL_NAME" | tr '[:upper:]' '[:lower:]')"
    DESC_LOWER="$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]')"

    if echo "$NAME_LOWER" | grep -qF "$KEYWORD_LOWER" || echo "$DESC_LOWER" | grep -qF "$KEYWORD_LOWER"; then
        # Truncate description if too long
        if [ ${#DESCRIPTION} -gt 65 ]; then
            DESCRIPTION="${DESCRIPTION:0:62}..."
        fi
        RELATIVE_PATH=".github/skills/${SKILL_NAME}/SKILL.md"
        printf "%-28s %-65s %s\n" "$SKILL_NAME" "$DESCRIPTION" "$RELATIVE_PATH"
        FOUND=$((FOUND + 1))
    fi
done

if [ "$FOUND" -eq 0 ]; then
    echo ""
    echo "No skills found matching: '$KEYWORD'"
    echo "Try broader keywords or list all: ls -d .github/skills/*/"
else
    echo ""
    echo "${FOUND} skill(s) found. Load a skill with: cat <Path>"
fi
