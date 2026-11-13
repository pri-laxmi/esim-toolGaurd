
from core.dependency_checker import (
    check_all_dependencies,
    print_dependency_report
)


def main():
    print("=" * 45)
    print("          eSim ToolGuard v1.0")
    print("=" * 45)

    print("\nInitializing dependency checker...")

    try:
        results = check_all_dependencies()
        print_dependency_report(results)

    except (FileNotFoundError, ValueError) as error:
        print(f"\nConfiguration Error: {error}")

    print("\nToolGuard execution completed!")


if __name__ == "__main__":
    main()
