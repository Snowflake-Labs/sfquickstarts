import sys
import re

# Required sections in the first and last steps
FIRST_STEP_TITLE = "Overview"
FIRST_STEP_SECTIONS = [
    {"What You'll Build", "What You Will Build"},
    {"What You'll Learn", "What You Will Learn"}
]
OPTIONAL_FIRST_STEP_SECTIONS = [
    {"What You'll Need", "What You Will Need"},
    {"Prerequisites"}
]  # At least one must be present
SNOWFLAKE_SIGNUP_URL = "https://signup.snowflake.com/"

LAST_STEP_TITLE = "Conclusion And Resources"
LAST_STEP_SECTIONS = [
    {"What You Learned"},
    {"Resources", "Related Resources"}
]

# Step label regex (ensures 1-4 words in Title Case)
STEP_LABEL_REGEX = r"^#+\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})$"

DEBUG = False

def validate_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.readlines()

    steps = {}
    current_section = None
    found_snowflake_signup = False

    for line in content:
        line = line.strip()

        # Detect main sections (##)
        if line.startswith("## "):
            current_section = line[3:].strip()
            if DEBUG:
                print(f"🔹 Section Found: {current_section}")
            steps[current_section] = []

        # Detect sub-sections (###) under the current section
        elif line.startswith("### ") and current_section:
            sub_section_name = line[4:].strip()
            if DEBUG:
                print(f"🔹 Sub-section Found: {sub_section_name}")
            steps[current_section].append(sub_section_name)

        # Check for Snowflake signup URL
        if SNOWFLAKE_SIGNUP_URL in line:
            found_snowflake_signup = True

    errors = []

    # Check the first step
    if not steps or FIRST_STEP_TITLE not in steps:
        errors.append(f"❌ First step must be '{FIRST_STEP_TITLE}', but it's missing.")
    else:
        detected_sections = {s.strip().title() for s in steps[FIRST_STEP_TITLE]}  # Preserve title case

        # Validate required sections (accepts either variation)
        for section_variants in FIRST_STEP_SECTIONS:
            if not any(variant in detected_sections for variant in section_variants):
                errors.append(f"❌ Missing required section in '{FIRST_STEP_TITLE}': {', '.join(section_variants)}")
        
        # Ensure at least one optional section is present (accepts either variation)
        if not any(any(variant in detected_sections for variant in section_variants) for section_variants in OPTIONAL_FIRST_STEP_SECTIONS):
            errors.append(f"❌ '{FIRST_STEP_TITLE}' must contain at least one of: {', '.join([', '.join(sec) for sec in OPTIONAL_FIRST_STEP_SECTIONS])}")

    # Check if Snowflake signup URL is present
    if not found_snowflake_signup:
        errors.append(f"❌ Missing required Snowflake signup/signin link in Prerequisites or What You Will Need under Overview: {SNOWFLAKE_SIGNUP_URL}")

    # Check the last step
    if not steps or LAST_STEP_TITLE not in steps:
        errors.append(f"❌ Last step must be '{LAST_STEP_TITLE}', but it's missing.")
    else:
        detected_sections = {s.strip().title() for s in steps[LAST_STEP_TITLE]}  # Normalize

        # Validate required sections (accepts either variation)
        for section_variants in LAST_STEP_SECTIONS:
            if not any(variant in detected_sections for variant in section_variants):
                errors.append(f"❌ Missing required section in '{LAST_STEP_TITLE}': {', '.join(section_variants)}")

    # Validate step labels for proper title case and word count
    for step in steps.keys():
        if not re.match(STEP_LABEL_REGEX, f"## {step}"):
            errors.append(f"❌ Step '{step}' must be 1-4 words long and in Title Case.")

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
