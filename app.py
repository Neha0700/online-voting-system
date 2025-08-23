from flask import Flask, redirect,render_template, request, url_for
from flask_mysqldb import MySQL
import datetime

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'Ganesh'
app.config['MYSQL_PASSWORD'] = 'Ganesh@2210'
app.config['MYSQL_DB'] = 'voting'

mysql = MySQL(app)
with app.app_context():
    db=mysql.connect
cursor = db.cursor()

@app.route('/')
def main():
    return render_template('main.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == "admin" and password == "password":
            print("Admin authenticated. Access granted.")
            return redirect(url_for('admin_panel'))
        else:
            print("Invalid admin credentials. Access denied.")
            return redirect(url_for('main'))

    return render_template('admin.html')

@app.route('/admin_panel', methods=['GET', 'POST'])
def admin_panel():
    return render_template('admin_panel.html')

@app.route('/create_new_election', methods=['GET', 'POST'])
def create_new_election():
    if request.method == 'GET':
        return render_template('create_new_election.html')

    elif request.method == 'POST':
        election_id = request.form.get('election_id')
        election_name = request.form.get('election_name')
        start_datetime = request.form.get('start_date')
        end_datetime = request.form.get('end_date')

        election_status = "active"

        try:
            start_datetime = datetime.datetime.strptime(start_datetime, "%Y-%m-%dT%H:%M")
            end_datetime = datetime.datetime.strptime(end_datetime, "%Y-%m-%dT%H:%M")
        except ValueError:
            print("Invalid datetime format. Please use YYYY-MM-DD HH:MM format.")
            return redirect(url_for('create_new_election'))
    
        try:
            cursor.execute("INSERT INTO elections (id, name, start_date, end_date, status) VALUES (%s, %s, %s, %s, %s)", (election_id, election_name, start_datetime, end_datetime, election_status))
            db.commit()
            
            num_candidates = int(request.form.get('num_candidates'))

            candidates = []
            for i in range(num_candidates):
                candidate_id = request.form.get(f'candidate_id{i}')
                candidate_name = request.form.get(f'candidate_name{i}')
                candidates.append((candidate_id, candidate_name))

            cursor.executemany("INSERT INTO candidates (id, name, votes) VALUES (%s, %s, 0)", candidates)
            db.commit()
            return redirect(url_for('create_new_election'))
        
        except mysql.connect.Error as err:
            print("Error:", err)
            return redirect(url_for('create_new_election'))

    return render_template('create_new_election.html')

@app.route('/show_results')
def show_results():
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id, name, votes FROM candidates")
        candidates = cursor.fetchall()
        
        if candidates:
            return render_template('show_results.html', candidates=candidates)
        else:
            return "No candidates found."
            
    except mysql.connect.Error as err:
        print("Error:", err)
        return "An error occurred while retrieving the results."


def stop_ongoing_election(election_id):
    try:
        cursor.execute("UPDATE elections SET status = 'stopped' WHERE id = %s", (election_id,))
        db.commit()
    except mysql.connector.Error as err:
        return f"Error stopping election: {err}"


def start_election_function(election_id):
    try:
        cursor.execute("UPDATE elections SET status = 'active' WHERE id = %s", (election_id,))
        db.commit()
    except mysql.connector.Error as err:
        return f"Error starting new election: {err}"


@app.route('/continue_previous_election', methods=['GET', 'POST'])
def continue_previous_election():
    try:
        cursor.execute("SELECT * FROM elections WHERE end_date >= CURDATE()")
        all_elections = cursor.fetchall()

        if all_elections:
            for election in all_elections:
                election_id, election_name, start_date, end_date, status = election
                if status == 'active':
                    message = f"Continuing Election: {election_name}"
                    cursor.execute("SELECT COUNT(*) FROM voters WHERE status = 0")
                    count = cursor.fetchone()[0]

                    if count > 0:
                        message += "All voters haven't voted in the election."
                    else:
                        message += "All voters have already voted in the election."

                    return render_template('stop_election.html', message=message, election_id=election_id)

            return render_template('continue_previous_election.html', message="No ongoing active elections found.")
        else:
            return render_template('start_election.html', message="No previous elections found.", start_new_election=True)
    except mysql.connector.Error as err:
        return render_template('continue_previous_election.html', message=f"Error: {err}")


@app.route('/stop_election', methods=['POST'])
def stop_election():
    election_id = request.form['election_id']
    stop_election = request.form['stop_election']

    if stop_election.lower() == "yes":
        result = stop_ongoing_election(election_id)
        if isinstance(result, str):
            message = result
        else:
            message = "The ongoing election has been stopped."
    else:
        message = "Continuing with the ongoing election."

    return render_template('stop_election.html', message=message)

@app.route('/start_election', methods=['POST'])
def start_election():
    start_new_election_input = request.form['start_new_election_input']

    if start_new_election_input.lower() == "yes":
        election_id = request.form['election_id']
        result = start_election_function(election_id)
        if isinstance(result, str):
            message = result
        else:
            message = " Election started."
    else:
        message = "No Election started."

    return render_template('start_election.html', message=message)

@app.route('/display_candidates')
def display_candidates():
    try:
        cursor.execute("SELECT id, name FROM candidates")
        candidates = cursor.fetchall()
        return render_template('display_candidates.html', candidates=candidates)
    except mysql.connector.Error as err:
        return render_template('error.html', message=f"Error: {err}")

@app.route('/vote', methods=['POST'])
def vote(user=[0]):
    voter_id = user[0]
    candidate_id = request.form['candidate_id']

    try:
        cursor = db.cursor()
        cursor.execute("SELECT status FROM voters WHERE id = %s", (voter_id,))
        voting_status = cursor.fetchone()

        if voting_status == 1:
            return "You have already voted."

        cursor.execute("UPDATE voters SET status = 1,candidate = %s WHERE id = %s", (candidate_id,voter_id,))
        db.commit()
        cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE id = %s", (candidate_id,))
        db.commit()

        return "Your vote has been recorded successfully."

    except mysql.connect.Error as err:
        print("Error:", err)
        return "An error occurred while recording your vote."

@app.route('/handle_voting', methods=['GET', 'POST'])
def handle_voting(user=[0]):
    if request.method == 'POST':
        try:
            cursor.execute("SELECT id, name FROM candidates")
            candidates = cursor.fetchall()
            return render_template('display_candidates.html', candidates=candidates)
        except mysql.connector.Error as err:
            return render_template('error.html', message=f"Error: {err}")
        
        voter_id = request.form['voter_id']
        candidate_id = request.form['candidate_id']
        
        cursor.execute("SELECT id FROM candidates")
        valid_candidate_ids = [str(candidate[0]) for candidate in cursor.fetchall()]
        
        if candidate_id not in valid_candidate_ids:
            return "Invalid candidate ID."
        vote(voter_id, candidate_id)
        return "Vote submitted successfully."
    return render_template('voting.html')

@app.route('/edit-vote', methods=['GET', 'POST'])
def edit_vote():
    if request.method == 'POST':
        voter_id = request.form['voter_id']

        
        cursor.execute("SELECT * FROM voters WHERE id = %s", (voter_id,))
        user = cursor.fetchone()

        if user:
            
            cursor.execute("SELECT id FROM candidates")
            valid_candidate_ids = [str(candidate[0]) for candidate in cursor.fetchall()]
            candidate_id = request.form['candidate_id']

            if candidate_id not in valid_candidate_ids:
                return "Invalid candidate ID."

            old_vote = user[6]

            try:
                
                cursor.execute("UPDATE candidates SET votes = votes - 1 WHERE id = %s", (old_vote,))
                db.commit()

                cursor.execute("UPDATE candidates SET votes = votes + 1 WHERE id = %s", (candidate_id,))
                db.commit()

                
                cursor.execute("UPDATE voters SET status = 1, candidate = %s WHERE id = %s", (candidate_id, voter_id))
                db.commit()

                return "Your vote has been successfully updated."

            except mysql.connector.Error as err:
                return "Error updating vote: " + str(err)
        
        else:
            return "Invalid voter ID."

    return render_template('edit_vote.html')


@app.route('/voter-panel', methods=['GET', 'POST'])
def voter_panel():
    if request.method == 'POST':
        aadhar = request.form['aadhar']
        
        cursor.execute("SELECT * FROM voters WHERE aadhar = %s", (aadhar,))
        user = cursor.fetchone()

        if user:
            
            user_info = {
                "id": user[0],
                "name": user[2],
                "age": user[3],
                "address": user[4]
            }

            cursor.execute("SELECT name, start_date, end_date, status FROM elections WHERE end_date >= CURDATE()")
            election_info = cursor.fetchone()

            if election_info:
                election_name, start_date, end_date, status = election_info

                if status == "active":
                    election_info = {
                        "election_name": election_name,
                        "start_date": start_date,
                        "end_date": end_date
                    }

                    if user[5] == 1:
                        voting_status = "Already Voted"
                        vote_decision = ""
                    else:
                        voting_status = "Not Voted Yet"
                        vote_decision = "yes"  

                    return render_template('voter_panel.html', user_info=user_info, election_info=election_info, voting_status=voting_status, vote_decision=vote_decision)

                else:
                    return "There is no ongoing election."

            else:
                return "No ongoing elections found."

        else:
            return "Invalid Aadhar Card number."

    return render_template('voter_panel_form.html')

if __name__ == "__main__":
    app.run(debug=True)