import sys
import re

# Required sections in the first and last steps
FIRST_STEP_TITLE = "Overview" 
FIRST_STEP_SECTIONS = {
    "### What You Will Build",
    "### What You Will Learn",
    "### Prerequisites",
    "### What You Will Need"
}
SNOWFLAKE_SIGNUP_URL = "https://signup.snowflake.com/"

LAST_STEP_TITLE = "Conclusion and Resources"
LAST_STEP_SECTIONS = {
    "Conclusion",
    "What You Learned",
    "Resources"
}

# Step label regex (ensures 1-4 words in Title Case)
STEP_LABEL_REGEX = r"^#+\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})$"

def validate_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.readlines()

    steps = {}
    current_step = None
    current_sections = set()
    found_snowflake_signup = False

    for line in content:
        line = line.strip()

        # Detect step headers (## Step Name)
        step_match = re.match(STEP_LABEL_REGEX, line)
        if step_match:
            # Save the previous step sections before moving to the next step
            if current_step:
                steps[current_step] = current_sections
            current_step = step_match.group(1)
            current_sections = set()
            continue

        # Detect section headers (### Section Name)
        if line.startswith("### "):
            section_name = line[4:].strip()
            current_sections.add(section_name)

        # Check for Snowflake signup URL
        if SNOWFLAKE_SIGNUP_URL in line:
            found_snowflake_signup = True

    # Save the last parsed step
    if current_step:
        steps[current_step] = current_sections

    errors = []

    # Check the first step
    step_titles = list(steps.keys())
    # Normalize and check for exact match for first step
    if not step_titles or FIRST_STEP_TITLE.lower() not in [step.lower() for step in step_titles[0:1]]:
        errors.append(f"❌ First step must be '{FIRST_STEP_TITLE}', but found '{step_titles[0]}' instead.")

    if FIRST_STEP_TITLE in steps:
        missing_sections = FIRST_STEP_SECTIONS - steps[FIRST_STEP_TITLE]
        if missing_sections:
            errors.append(f"❌ Missing sections in '{FIRST_STEP_TITLE}': {', '.join(missing_sections)}")

    if not found_snowflake_signup:
        errors.append(f"❌ Missing required Snowflake signup link: {SNOWFLAKE_SIGNUP_URL}")

    # Check the last step
    if not step_titles or LAST_STEP_TITLE not in [step for step in step_titles[-1:]]:
        errors.append(f"❌ Last step must be '{LAST_STEP_TITLE}', but found '{step_titles[-1]}' instead.")

    if LAST_STEP_TITLE in steps:
        missing_sections = LAST_STEP_SECTIONS - steps[LAST_STEP_TITLE]
        if missing_sections:
            errors.append(f"❌ Missing sections in '{LAST_STEP_TITLE}': {', '.join(missing_sections)}")

    # Validate step labels for proper title case and word count
    for step in step_titles:
        if not re.match(STEP_LABEL_REGEX, f"## {step}"):
            errors.append(f"❌ Step '{step}' must be 2-3 words long and in Title Case.")

    if errors:
        print("\n".join(errors))
        sys.exit(1)
    else:
        print(f"✅ {file_path} passed all validations.")

if __name__ == "__main__":
    files_to_check = sys.argv[1:]
    if not files_to_check:
        print("No markdown files provided for validation.")
        sys.exit(0)

    for md_file in files_to_check:
        print(f"🔍 Validating {md_file}...")
        validate_markdown(md_file)
