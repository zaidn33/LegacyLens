
# Python implementation of the Logic Map
def print_hello_world():
    # Initialize the iteration counter and the maximum iterations
    iteration_counter = 0
    max_iterations = 5
    greeting_message = 'HELLO, WORLD!'

    # Perform the print procedure until the iteration counter equals the maximum iterations
    while iteration_counter < max_iterations:
        # Increment the iteration counter by 1
        iteration_counter += 1
        
        # Display the current iteration counter and the greeting message to the console
        print(f'Iteration {iteration_counter}: {greeting_message}')

    # Stop the program once the maximum iterations are reached
    return

# Call the function to start the program
print_hello_world()
