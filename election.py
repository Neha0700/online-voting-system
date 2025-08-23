import mysql.connector
import time
import datetime

db = mysql.connector.connect(
    host="localhost",
    user="Ganesh",
    password="Ganesh@2210",
    database="voting"
)
cursor = db.cursor()

def authenticate_admin():
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")

    if username == "admin" and password == "password":
        print("Admin authenticated. Access granted.")
        admin_panel()
    else:
        print("Invalid admin credentials. Access denied.")

def admin_panel():
    while True:
        print("\nAdmin Panel:")
        print("1. Create New Election")
        print("2. Continue Previous Election")
        print("3. Give Results")
        print("4. Exit")
        choice = input("Enter your choice: ")
        
        if choice == "1":
            create_new_election()
            pass
        elif choice == "2":
            continue_previous_election()
            pass
        elif choice == "3":
            show_results()
            pass
        elif choice == "4":
            print("Exiting admin panel...")
            break
        else:
            print("Invalid choice. Please try again.")

def create_new_election():
    election_id = input("Enter the ID of the new election: ")
    election_name = input("Enter the name of the new election: ")
    start_datetime_input = input("Enter the start datetime of the election (YYYY-MM-DD HH:MM:SS): ")
    end_datetime_input = input("Enter the end datetime of the election (YYYY-MM-DD HH:MM:SS): ")

    election_status = "active"

    try:
        start_datetime = datetime.datetime.strptime(start_datetime_input, "%Y-%m-%d %H:%M:%S")
        end_datetime = datetime.datetime.strptime(end_datetime_input, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        print("Invalid datetime format. Please use YYYY-MM-DD HH:MM:SS format.")
        return
    
    try:
        cursor.execute("INSERT INTO elections (id, name, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s)", (election_id, election_name, start_datetime, end_datetime, election_status))
        db.commit()
        print("New election created successfully.")
        num_candidates = int(input("Enter the number of candidates: "))
        candidates = []
        for i in range(num_candidates):
            candidate_id = input(f"Enter the ID of candidate {i + 1}: ")
            candidate_name = input(f"Enter the name of candidate {i + 1}: ")
            candidates.append((candidate_id, candidate_name))

        cursor.executemany("INSERT INTO candidates (id, name, votes) VALUES (%s, %s, 0)", candidates)
        db.commit()
        print("Candidate information added successfully.")
        
    except mysql.connector.Error as err:
        print("Error:", err)

def show_results():
    try:
        cursor.execute("SELECT id, name, votes FROM candidates")
        candidates = cursor.fetchall()
        
        if candidates:
            print("\nElection Results:")
            for candidate in candidates:
                print(f"Candidate ID: {candidate[0]}, Name: {candidate[1]}, Votes: {candidate[2]}")
        else:
            print("No candidates found.")
            
    except mysql.connector.Error as err:
        print("Error:", err)

def stop_ongoing_election(election_id):
    try:
        cursor.execute("UPDATE elections SET status = 'stopped' WHERE id = %s", (election_id,))
        db.commit()
    except mysql.connector.Error as err:
        print("Error stopping the ongoing election:", err)
        
def start_new_election_function(election_id):
    try:
        cursor.execute("UPDATE elections SET status = 'active' WHERE id = %s", (election_id,))
        db.commit()
        print("The Election started successfully.")
    except mysql.connector.Error as err:
        print("Error starting the new election:", err)

def continue_previous_election():
    try:
        cursor.execute("SELECT * FROM elections WHERE end_date >= CURDATE()")
        all_elections = cursor.fetchall()
        
        if all_elections:
            for election in all_elections:
                election_id, election_name, start_date, end_date, status = election
                if status == 'active':
                    print(f"\nContinuing Election: {election_name}")
                    cursor.execute("SELECT COUNT(*) FROM voters WHERE status = 0")
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        print("All voters haven't voted in the election.")
                    else:
                        print("All voters have already voted in the election.")
                        
                    stop_election = input("Do you want to stop the ongoing election? (yes/no): ")
                    if stop_election.lower() == "yes":
                        stop_ongoing_election(election_id)
                        print("The ongoing election has been stopped.")
                    else:
                        print("Continuing with the ongoing election.")
                    break
            else:
                print("No ongoing active elections found.")
                print("Previous elections are available.")
                start_new_election_input = input("Do you want to start a Previous Election? (yes/no): ")
                if start_new_election_input.lower() == "yes":
                    id = input("Enter the Election ID: ")
                    start_new_election_function(id)
                else:
                    print("No Election started.")
        else:
            print("No previous elections found.")
    except mysql.connector.Error as err:
        print("Error:", err)

def display_candidates():
    cursor.execute("SELECT id, name FROM candidates")
    candidates = cursor.fetchall()
    
    print("\nList of Candidates:")
    for candidate in candidates:
        print(f"{candidate[0]}. {candidate[1]}")
        
def vote_for_candidate(voter_id, candidate_id):
    try:
        cursor.execute("SELECT status FROM voters WHERE id = %s", (voter_id,))
        voting_status = cursor.fetchone()[0]
        
        if voting_status == 1:
            print("You have already voted.")
            return
        cursor.execute("UPDATE voters SET status = 1,candidate = %s WHERE id = %s", (candidate_id,voter_id,))
        db.commit()
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE id = %s", (candidate_id,))
        db.commit()
        print("Your vote has been recorded successfully.")
    except mysql.connector.Error as err:
        print("Error:", err)

def handle_voting(voter_id):
    display_candidates()
    
    candidate_id = input("Enter the ID of the candidate you want to vote for: ")
    cursor.execute("SELECT id FROM candidates")
    valid_candidate_ids = [str(candidate[0]) for candidate in cursor.fetchall()]
    if candidate_id not in valid_candidate_ids:
        print("Invalid candidate ID.")
        return
    vote_for_candidate(voter_id, candidate_id)
    
def edit_vote(voter_id):
    cursor.execute("SELECT * FROM voters WHERE id = %s", (voter_id,))
    user = cursor.fetchone()
    if user:
        display_candidates()
        candidate_id = input("Enter the ID of the candidate you want to change your vote to: ")
        cursor.execute("SELECT id FROM candidates")
        valid_candidate_ids = [str(candidate[0]) for candidate in cursor.fetchall()]
        if candidate_id not in valid_candidate_ids:
            print("Invalid candidate ID.")
            return
        old_vote = user[6]
        try:
            cursor.execute("UPDATE candidates SET votes = votes - 1 WHERE id = %s", (old_vote,))
            db.commit()
            cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE id = %s", (candidate_id,))
            db.commit()
            print("Your vote has been successfully updated.")
            cursor.execute("UPDATE voters SET status = 1, candidate = %s WHERE id = %s", (candidate_id, voter_id))
            db.commit()
        except mysql.connector.Error as err:
            print("Error updating vote:", err)
        
def voter_panel():
    aadhar = input("Enter your Aadhar Card number: ")
    cursor.execute("SELECT * FROM voters WHERE aadhar = %s", (aadhar,))
    user = cursor.fetchone()
    
    if user:
        print("Welcome,", user[1])
        print("Your credentials:")
        print("Name:", user[2])
        print("Age:", user[3])
        print("Address:", user[4])
        
        cursor.execute("SELECT name, start_date, end_date, status FROM elections WHERE end_date >= CURDATE()")
        election_info = cursor.fetchone()
        
        if election_info:
            election_name, start_date, end_date, status = election_info
            if status == "active":
                print("Election Name:", election_name)
                print("Start Date:", start_date.strftime("%Y-%m-%d %H:%M:%S"))  
                print("End Date:", end_date.strftime("%Y-%m-%d %H:%M:%S"))
                
                if user[5] == 1:
                    print("Voting Status: Already Voted")
                    print("You have already voted.")
                else:
                    print("Voting Status: Not Voted Yet")
                    vote = input("Do you want to vot..? (yes/no): ")
                    if vote.lower() == "yes":
                        handle_voting(user[0]) 
                    else:
                        print("Thank you for your response.")

                    edit = input("Do you want to edit vote..? (yes/no): ")
                    if edit == "yes":
                        edit_vote(user[0])
                    else:
                        print(" ")
            else:
                print("There is no ongoing election.")
        else:
            print("No ongoing elections found.")
    else:
        print("Invalid Aadhar Card number.")
   
def main():
    while True:
        print("\nOnline Voting System:")
        print("1. Admin Panel")
        print("2. Voter Panel")
        print("3. Exit")
        choice = input("Enter your choice: ")
        
        if choice == "1":
            authenticate_admin()
        elif choice == "2":
            voter_panel()
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
