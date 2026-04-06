import sys

def display_header():
    print("--- Program Header ---")

def display_user_info(userName, userAge):
    print(f"User Name: {userName}")
    print(f"User Age: {userAge}")

def process_counter_loop(userAge):
    counter = 1
    while counter <= 3:
        print(f"Counter: {counter}")
        counter += 1

    if userAge >= 18:
        print("STATUS: ADULT")
    else:
        print("STATUS: MINOR")

def display_completion_message():
    print("PROGRAM COMPLETE.")

def main():
    # Placeholder values for demonstration
    userName = "Alice"
    userAge = 25

    display_header()
    display_user_info(userName, userAge)
    process_counter_loop(userAge)
    display_completion_message()

if __name__ == "__main__":
    main()
