from ui.menu import Menu

def main():
    """Main application entry point"""
    try:
        menu = Menu()
        menu.display_main_menu()
    except KeyboardInterrupt:
        print("\nProgram interrupted. Exiting...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()