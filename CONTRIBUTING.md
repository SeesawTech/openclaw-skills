# Collaboration Standards

## Permissions
- **Admin (Ikaros)**: Direct write access to `main`.
- **AIAgent Team**: Pull Request (PR) access only. Direct commits to `main` are disabled for team members.

## Workflow
1. **Fork/Branch**: Create a feature branch for your new skill or update.
2. **Standard Format**: Every skill MUST follow the standard structure:
   - `skills/<skill-name>/SKILL.md` (Required)
   - `skills/<skill-name>/scripts/` (Optional)
   - `skills/<skill-name>/references/` (Optional)
   - `skills/<skill-name>/assets/` (Optional)
3. **Validation**: Use `scripts/package_skill.py <path-to-skill>` to validate your skill before submitting a PR.
4. **Pull Request**: Open a PR to `main`. Ikaros (Admin) or a team lead will review and merge.

## Naming Conventions
- Skill directories must use `lowercase-hyphen-case` (e.g., `my-cool-skill`).
- Skill names in `SKILL.md` frontmatter should match the directory name.

## Best Practices
- **Concise**: Keep `SKILL.md` body focused on instructions. Move large datasets or long documentation to the `references/` folder.
- **Deterministic**: Use scripts in `scripts/` for tasks that require high reliability.
- **Privacy**: Never include API keys, passwords, or PII in the repository.
