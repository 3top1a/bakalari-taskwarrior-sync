from taskw import TaskWarriorShellout
import requests
import getopt
import sys
import time
import datetime

#------- Bakalari

# Load bakalari

# Gets the accesstoken. Returns access token


def bakalrari_get_token(server, password, username):
	_url = server + "/api/login"
	header = {'Content-Type': 'application/x-www-form-urlencoded'}
	params = {'grant_type': 'password', 'client_id': 'ANDR',
			  'username': username, 'password': password}

	try:
		r = requests.post(url=_url, headers=header, data=params)
	except requests.exceptions.ConnectionError:
		print("Connection error")
		exit()
	data = r.json()
	access_token = data.get('access_token')
	return access_token


# Load bakalari planned marks

def bakalari_get_planned_marks(server, token):
	_url = server + "/api/3/marks"
	header = {'Content-Type': 'application/x-www-form-urlencoded',
			  'Authorization': 'Bearer ' + token}
	params = {}

	# Request it
	try:
		r = requests.get(url=_url, headers=header, data=params)
	except ConnectionError:
		print("Connection error")
		exit()
	data = r.json()

	# Parse
	blank_marks = []

	subjects = data.get("Subjects")
	for subject in subjects:
		marks = subject.get("Marks")
		for mark in marks:
				blank_marks.append(mark)

	return blank_marks


# Load bakalari homework

def bakalari_get_planned_homework(server, token):
	_url = server + "/api/3/homeworks"
	header = {'Content-Type': 'application/x-www-form-urlencoded',
			'Authorization': 'Bearer ' + token}
	params = {'to': "9999-12-30"}

	# Request it
	try:
		r = requests.get(url=_url, headers=header, data=params)
	except ConnectionError:
		print("Connection error")
		exit()
	data = r.json()

	# Parse
	homeworks = data.get('Homeworks')

	return homeworks

#-------- Taskwarrior

# Load tasks

def load_tasks():
	w = TaskWarriorShellout()
	data = w.load_tasks()
	pending = data.get("pending")
	completed = data.get("completed")

	return pending, completed, w


#-------- Main
def main():
	try:
		opts, args = getopt.gnu_getopt(sys.argv[1:], "hs:p:u:", [
			"server", "password", "username"])
	except getopt.GetoptError:
		print('main.py -s example.bakalari.cz -p password -u username')
		sys.exit(1)
	server = ""
	password = ""
	username = ""

	for opt, arg in opts:
		if opt == '-h':
			print('bakatask.py -s example.bakalari.cz -p password -u username')
			sys.exit()
		elif opt in ("-s", "--server"):
			server = arg
		elif opt in ("-p", "--password"):
			password = arg
		elif opt in ("-u", "--username"):
			username = arg

	token = bakalrari_get_token(server, password, username)

	homeworks = bakalari_get_planned_homework(server, token)
	blank_marks = bakalari_get_planned_marks(server, token)

	pending, completed, w = load_tasks()

	# Naming: 🏫[{1}{2}] {3}
	# {1} H for homework, M for mark
	# {2} ID
	# {3} Name

	# Goals
	# Create homework tasks
	# Complete done or closed homework
	for homework in homeworks:
		"""
		Exists in taskw
			Completed in taskw -> do nothing
			Not completed -> complete it if completed on Bakalari
		Does not and is not completed on bakalari -> creates
		"""

		if is_in_completed(completed, homework):
			continue

		# If in pending
		if is_in_pending(pending, homework, w):
			continue

		# If neither
		## Complete task if completed on bakalari
		## Add to taskw otherwise

		if not (homework["Done"] or homework["Closed"] or homework["Finished"]):
			w.task_add(
				"🏫[{}{}] {}".format("H", homework["ID"], homework["Content"]),
				priority="H",
				project="skola",
				due=str(
					(time.mktime(
						datetime.datetime.fromisoformat(homework["DateEnd"])
					.timetuple()))
				)
			)
			# TODO due dates

		print(homework)

def is_in_completed(completed, homework):
	# If in completed
	school_tasks = [a for a in completed if a["description"].startswith("🏫[H") ]
	for s_task in school_tasks:
		if [a for a in school_tasks if task_is_homework(a, homework) ]:
			return True
	return False

def is_in_pending(pending, homework, w):
	r = False
	school_tasks = [a for a in pending if (
		a["description"].startswith("🏫[H") and a["status"] != "completed"
	)]
	for s_task in school_tasks:
		if [a for a in school_tasks if task_is_homework(a, homework) ]:
			if homework["Done"] or homework["Closed"] or homework["Finished"]:
				try:
					w.task_done(id=s_task["id"])
					r = True
				except:
					pass
	return True


def task_is_homework(task, homework):
	# task: Task, with name
	# homework: Homework array with name and ID
	name = str(task["description"])
	name = name[3:].split(']')[0]

	if name == homework["ID"]:
		return True

	return False

if __name__ == "__main__":
	main()
