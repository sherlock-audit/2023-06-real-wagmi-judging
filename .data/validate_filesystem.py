import os
import re


def main():
    try:
        total_issues = int(os.environ.get("TOTAL_ISSUES"))
    except:
        print("TOTAL_ISSUES secret not set.")
        return

    # Store all the errors found
    errors = []
    # Store all the issues read
    issues = []

    def process_directory(path):
        nonlocal issues
        print("Directory %s" % path)

        # Get the items in the directory
        items = [
            x
            for x in os.listdir(path)
            if x not in [".data", ".git", ".github", "README.md", "Audit_Report.pdf", ".gitkeep"]
        ]

        directory_has_report = False
        for item in items:
            print("- Item %s" % item)
            is_dir = os.path.isdir(os.path.join(path, item))

            if is_dir:
                matches = [
                    r"^(H|M|High|Medium)-\d+$",
                    r"^\d+-(H|M|High|Medium)$",
                    r"^false$",
                    r"^invalid$",
                ]
                correctly_formatted = any(
                    re.match(pattern, item, re.IGNORECASE) for pattern in matches
                )
                if (
                    not any([x in path for x in ["invalid", "false"]])
                    and not correctly_formatted
                ):
                    errors.append("Directory %s is not formatted properly." % item)
                else:
                    process_directory(os.path.join(path, item))
            else:
                if not re.match(r"^\d+(-best)?.md$", item):
                    errors.append("File %s is not formatted properly." % item)
                    continue

                # Check if the file is the best report
                if "-best" in item:
                    if not directory_has_report:
                        directory_has_report = True
                    else:
                        errors.append(
                            "Directory %s has multiple best reports marked." % path
                        )

                # Extract issue number from the file name
                issue_number = int(re.match(r"(\d+)", item).group(0))

                # Check if the issue was already found
                if issue_number in issues:
                    errors.append("Issue %s exists multiple times." % issue_number)
                else:
                    issues.append(issue_number)

        if (
            path != "."
            and not any(x in path for x in ["invalid", "false"])
            and not directory_has_report
        ):
            errors.append("Directory %s does not have a best report selected." % path)

    # Start processing from the root
    process_directory(".")

    expected_issues = [x + 1 for x in range(total_issues)]
    # Check if all issues are found in the repo
    for x in expected_issues:
        if x not in issues:
            errors.append("Issue %s not found in the repo." % x)
    # Check if there are no additional issues added
    for x in issues:
        if x not in expected_issues:
            errors.append("Issue %s should not be in the repo." % x)

    if len(errors) > 0:
        for error in errors:
            print("❌ %s" % error)
        exit(1)

    print("✅ Repo structure is valid.")


if __name__ == "__main__":
    main()
