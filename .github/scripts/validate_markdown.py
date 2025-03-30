import sys
import re

# Required sections for Overview and Conclusion steps
REQUIRED_OVERVIEW_SECTIONS = [
    "Overview",
    "What You Will Build",
    "What You Will Learn",
    "Prerequisites",
    "What You Will Need"
]
REQUIRED_CONCLUSION_SECTIONS = [
    "Conclusion",
    "What You Learned",
    "Resources"
]
SNOWFLAKE_SIGNUP_LINK = "https://signup.snowflake.com/"

# Regex for title case step labels (2-3 words)
STEP_LABEL_REGEX = re.compile(r"^#+\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})$")

def validate_markdown_file(filepath):
    """Validates the structure of a single markdown file."""
    with open(filepath, "r", encoding="utf-8") as file:
        lines = file.readlines()

    errors = []
    step_labels = []
    current_step = None
    overview_found = False
    conclusion_found = False
    overview_sections = set()
    conclusion_sections = set()
    snowflake_link_found = False

    for line in lines:
        line = line.strip()

        # Detect step headers (H2 or higher)
        match = STEP_LABEL_REGEX.match(line)
        if match:
            step_labels.append(match.group(1))
            current_step = match.group(1)

        # Check required sections under Overview
        if current_step == "Overview":
            overview_found = True
            for section in REQUIRED_OVERVIEW_SECTIONS:
                if section in line:
                    overview_sections.add(section)
            if SNOWFLAKE_SIGNUP_LINK in line:
                snowflake_link_found = True

        # Check required sections under Conclusion and Resources
        if current_step == "Conclusion and Resources":
            conclusion_found = True
            for section in REQUIRED_CONCLUSION_SECTIONS:
                if section in line:
                    conclusion_sections.add(section)

    # Validate Overview step
    if not overview_found:
        errors.append(f"❌ {filepath}: Missing 'Overview' step at the beginning.")
    elif not overview_sections.issuperset(REQUIRED_OVERVIEW_SECTIONS):
        errors.append(f"❌ {filepath}: 'Overview' step is missing sections: {set(REQUIRED_OVERVIEW_SECTIONS) - overview_sections}")
    if not snowflake_link_found:
        errors.append(f"❌ {filepath}: Missing Snowflake signup link in 'Prerequisites' or 'What You Will Need'.")

    # Validate Conclusion and Resources step
    if not conclusion_found:
        errors.append(f"❌ {filepath}: Missing 'Conclusion and Resources' step at the end.")
    elif not conclusion_sections.issuperset(REQUIRED_CONCLUSION_SECTIONS):
        errors.append(f"❌ {filepath}: 'Conclusion and Resources' step is missing sections: {set(REQUIRED_CONCLUSION_SECTIONS) - conclusion_sections}")

    # Validate step labels
    for label in step_labels:
        if not STEP_LABEL_REGEX.match(label):
            errors.append(f"❌ {filepath}: Step label '{label}' should be 2-3 words long and in Title Case.")

    if errors:
        print("\n".join(errors))
        sys.exit(1)  # Fail the job

if __name__ == "__main__":
    md_files = sys.argv[1:]  # Get the list of changed .md files
    if not md_files:
        print("✅ No markdown files to validate.")
        sys.exit(0)

    for md_file in md_files:
        validate_markdown_file(md_file)

    print("✅ All modified markdown files passed validation!")
