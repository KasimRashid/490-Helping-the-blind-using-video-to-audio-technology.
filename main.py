from geometry import rectangle_size, get_color_description
from detection import DetectedRectangle
import sys


def main():
    #Variable to hold the narration
    narrating = False

    while True:
        print("\n*** OBJECT DETECTION MAIN MENU ***")
        print("1. Start Narrating")
        print("2. Stop Narrating")
        print("3. Simulate Detection (Shape, Color, Size)")
        print("4. Exit")
        
        choice = input("\nEnter menu choice: ")

        if choice == '1':
            narrating = True
            print("\nNarration started. The app is accessing the camera.")
        
        elif choice == '2':
            narrating = False
            print("\nNarration stopped.")

        elif choice == '3':
            if not narrating:
                print("\nError: You must start narration first.")
                continue
            
            # Simulated data input for shape, color, and size
            # In a live app, this data would come from the camera feed.
            color = input("\nEnter detected color: ")
            l = float(input("Enter length: "))
            w = float(input("Enter width: "))
            
            obj = DetectedRectangle(length=l, width=w, color=color) [25]
            # Dictate the findings to the user [5]
            print(f"\n[AUDIO OUT]: {obj.get_narrative()}")

        elif choice == '4':
            break
        
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()