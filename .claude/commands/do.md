# /do Command

Do "$ARGUMENTS" part of the plan. IMPORTANT! Don't do other parts of the plan.

## Usage
```
/do [specific action point or plan section]
```

## Description
This command executes a specific part of the plan. When finished:
- Mark relevant action points as done in the plan file
- Update the plan file with a concise summary of what's done
- Keep the plan file concise and clear by replacing/removing obsolete info
- Ensure we are NOT on the main branch and make a commit with a short message

## Important Notes
- Only work on the specified part of the plan
- Don't proceed to other parts automatically
- Ask for clarification if unsure about anything
- Always commit changes with descriptive messages

## Example
```
/do implement filter UI components
/do add database migration
/do write unit tests for new feature
```