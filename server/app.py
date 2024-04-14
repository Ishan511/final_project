from flask import Flask,g,request,render_template,session,flash,redirect,url_for,send_file
import xml.etree.ElementTree as ET
import sqlite3
from io import BytesIO
# import socket


app = Flask(__name__)
app.config["SECRET_KEY"] = "ThisisSecret!"


# def get_free_port():
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.bind(('localhost', 0))
#     _, port = s.getsockname()
#     s.close()
#     return port


############### DB CONNECTIONS ########################
def connect_db():
    sql = sqlite3.connect('/Users/ishanunnarkar/Desktop/Projects/Bug_Hound-Project-main/server/db/bughound.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_db():
    if not hasattr(g,"sqlite3"):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g,'sqlite_db'):
        g.sqlite_db.close()

################## INDEX, LOGIN, LOGOUT #####################
@app.route("/index_page",methods=["GET"])
def index_page():
    if "loggedin" in session:
        condition = False
        if session['user_level']==3:
            condition=True
    return render_template('index.html',condition=condition,name=session["username"],userlevel=session["user_level"])
@app.route("/",methods=["GET","POST"])
def index():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = str(request.form['username'])
        password = str(request.form['password'])
        db = get_db()
        query = 'SELECT * FROM employees WHERE username = "{0}" and password ="{1}"'.format(username,password)
        cur = db.execute(query)
        account = cur.fetchall()
        if account:
            session['loggedin'] = True
            session['id'] = account[0]["emp_id"]
            session['username'] = account[0]["username"]
            session['user_level'] = account[0]["userlevel"]
            condition = False
            if session['user_level']==3:
                condition=True
            return render_template('index.html',condition=condition,name=session["username"],userlevel=session["user_level"])
        else:
            return render_template("login.html",msg="True")
    return render_template('login.html')

@app.route('/logout')
def logout():
    if "loggedin" in session:
        session.pop('loggedin', None)
    else:
        flash("You must be logged in first")
    return render_template("login.html")

########### HELPER FUNCTIONS #########################
def get_programs():
    db=get_db()
    cur = db.execute('select * from programs')
    programs = cur.fetchall()
    return programs

def get_employees():
    db=get_db()
    cur = db.execute('select * from employees')
    employees = cur.fetchall()
    return employees

def get_area():
    db = get_db()
    cur = db.execute("select * from areas")
    areas = cur.fetchall()
    return areas
####################### BUG######################

@app.route("/add_bug",methods=["GET","POST"])
def add_bug():
    ##options for form
    programs = get_programs()
    areas = get_area()
    employees = get_employees()
    # report_options = ["Coding Error","Design Issue","Suggestion","Documentation","Hardware","Query"]
    # severity = ["Minor", "Serious", "Fatal"]
    status=["open","closed","resolved"]
    priority = [1,2,3,4,5,6]
    # resolution = ["Pending","Fixed","Irreproducible","Deferred","As designed","Withdrawn by reporter","Need more info",\
    #               "Disagree with suggestion","Duplicate"]
    if "loggedin" not in session:
        return render_template("login.html")
    if request.method=="POST":
        form_data = request.form.to_dict()
        columns = []
        values = []
        placeholders= []
        for key, value in form_data.items():
            if value:
                columns.append(key)
                values.append(value)
                placeholders.append("?")
        if request.form['program_options']:
            db = get_db()
            query = f"INSERT INTO bugs ({', '.join(columns)}) VALUES ({','.join(placeholders)})"
            db.execute(query,values)
            db.commit()
            return redirect(url_for("add_bug"))
        else:
            return render_template("add_bug.html",program_options=programs,\
                           employees=employees,\
                            areas=areas,status=status,priority=priority,\
                                condition=True)

        
    
    #entry_date = datetime.datetime.now().strftime("%m/%d/%Y")
    return render_template("add_bug.html",program_options=programs,\
                           employees=employees,\
                            areas=areas,status=status,priority=priority)


@app.route("/view_attachment",methods=["GET","POST"])
def view_attachment():
    if "loggedin" not in session:
        return render_template("login.html")
    if request.method=="POST":
        option = request.form['options']
        db = get_db()
        cur = db.execute(f"select * from attach where attach_id={option}")
        data=cur.fetchall()
            
        return send_file(BytesIO(data[0][3]), download_name=data[0][2], as_attachment=True)
    

@app.route("/upload_attachment/<bug_id>",methods=["GET","POST"])
def upload_attachment(bug_id):
    if "loggedin" not in session:
        return render_template("login.html")
    db = get_db()
    file = request.files['file']
    filename = file.filename
    data = file.read()
    query = 'INSERT INTO attach (bug_id,filename,file) VALUES (?, ?,?)'
    db.execute(query,(bug_id,filename,data))
    db.commit()
    return redirect(url_for("update_bug",bug_id=bug_id))

@app.route("/update_bug/<bug_id>",methods=["GET","POST"])
def update_bug(bug_id):
    if "loggedin" not in session:
        return render_template("login.html")
    db = get_db()
    if request.method == "POST":
        form_data = request.form.to_dict()
        columns = []
        values = []
        placeholders= []
        for key, value in form_data.items():
            if value:
                columns.append(key)
                values.append(value)
                placeholders.append("?")
        
        sql_query = "UPDATE bugs SET "
        for i, col in enumerate(columns):
            sql_query += f"{col} = {placeholders[i]}"
            if i != len(columns) - 1:
                sql_query += ", "
        sql_query += " WHERE bug_id = ?"
        db.execute(sql_query,values+[bug_id])
        db.commit()
        return redirect(url_for("update_bug",bug_id=bug_id))

    
    query = f"select * from bugs where bug_id={bug_id}"
    cur = db.execute(query)
    data = cur.fetchall()
    programs = get_programs()
    employees = get_employees()
    areas = get_area()
    # report_options = ["Coding Error","Design Issue","Suggestion","Documentation","Hardware","Query"]
    # severity = ["Minor", "Serious", "Fatal"]
    status=["open","closed","resolved"]
    priority = [1,2,3,4,5,6]
    # resolution = ["Pending","Fixed","Irreproducible","Deferred","As designed","Withdrawn by reporter","Need more info",\
    #               "Disagree with suggestion","Duplicate"]
    attach_cur = db.execute(f'select * from attach where bug_id={bug_id}')
    attach = attach_cur.fetchall()
    # return render_template("update_bug.html",bug_id=bug_id,data=data,programs=programs,report_options=report_options,\
    #                        severity=severity,employees=employees,areas=areas,\
    #                         status=status,priority=priority,resolution=resolution,attach=attach)
    return render_template("update_bug.html",bug_id=bug_id,data=data,programs=programs,\
                           employees=employees,areas=areas,\
                            status=status,priority=priority,attach=attach)

@app.route("/result_bug",methods=["GET","POST"])
def result_bug():
    if "loggedin" not in session:
        return render_template("login.html")
    program = request.form['program_options']
    # report_type = request.form['report_options']
    # severity = request.form['severity']
    areas = request.form['areas']
    assigned_to = request.form['assigned_to']
    reported_by = request.form['reported_by']
    status = request.form['status']
    priority = request.form['priority']
    # resolution = request.form['resolution']
    db=get_db()
    query = "SELECT * FROM bugs WHERE "
    if program != 'ALL':
        query += f"problem_summary = '{program}' AND "
    # if report_type != 'ALL':
    #     query += f"report_type = '{report_type}' AND "
    # if severity != 'ALL':
    #     query += f"severity = '{severity}' AND "
    if areas != 'ALL':
        query += f"areas = '{areas}' AND "
    if assigned_to != 'ALL':
        query += f"assigned_to = '{assigned_to}' AND "
    if reported_by != 'ALL': 
        query += f"reported_by = '{reported_by}' AND "
    if status != 'ALL':
        query += f"status = '{status}' AND "
    if priority != 'ALL':
        query += f"priority = '{priority}' AND "
    # if resolution != 'ALL':
    #     query += f"resolution = '{resolution}' AND "
    query = query[:-5]
    results = db.execute(query)
    data = results.fetchall()
    return render_template("result_bug.html",data=data)

@app.route("/search_bug",methods=["GET","POST"])
def search_bug():
    if "loggedin" not in session:
        return render_template("login.html")
    db=get_db()
    employee = get_employees()
    query = 'select * from bugs'
    cur = db.execute(query)
    data= cur.fetchall()
    programs =[i[1] for i in data]
    areas = get_area()
    area = [i for i in areas]
    assigned_to=[i[2] for i in employee]
    reported_by=[i[2] for i in employee]
    status=["open","closed","resolved"]
    report_type = ["Coding Error","Design Issue","Suggestion","Documentation","Hardware","Query"]
    severity = ["Minor", "Serious", "Fatal"]
    status=["open","closed","resolved"]
    priority = [1,2,3,4,5,6]
    resolution = ["Pending","Fixed","Irreproducible","Deferred","As designed","Withdrawn by reporter","Need more info",\
                  "Disagree with suggestion","Duplicate"]
    # return render_template("search_bug.html",programs=programs,report_type=report_type,severity=severity,\
    #                        area=area,assigned_to=assigned_to,reported_by=reported_by,status=status,\
    #                         priority=priority,resolution=resolution)
    return render_template("search_bug.html",programs=programs, \
                           area=area,assigned_to=assigned_to,reported_by=reported_by,status=status,\
                            priority=priority)



################## DATABASE MAINTENANCE ##########################
@app.route("/database_maintenance")
def database_maintenance():
    return render_template("database_maintenance.html")

######################## EMPLOYEE #######################
#Employee Functions
#add employee
@app.route("/add_employee",methods=["GET","POST"])
def add_employee():
    if "loggedin" not in session:
        return render_template("login.html")
    if request.method == "GET":
        return render_template("add_employess.html")
    
    name = request.form["name"]
    username = request.form["user_name"]
    password = request.form["password"]
    user_level = request.form["user_level"]
    if name and username and password and user_level:
        db=get_db()
        db.execute('insert into employees (name,username,password,userlevel) values(?,?,?,?)',[name,username,password,user_level] )
        db.commit()
        return render_template("add_employess.html",condition="True",name=name,condition1=False)
    else:
        return render_template("add_employess.html",condition1=True)



@app.route("/process_update_employee",methods=["POST"])
def process_update_employee():
    if "loggedin" not in session:
        return render_template("login.html")
    emp_id = request.form["emp_id"]
    name = request.form["name"]
    username = request.form["username"]
    password = request.form["password"]
    user_level = request.form["user_level"]


    update_query = f"UPDATE employees SET name='{name}',username='{username}',password='{password}',userlevel='{user_level}' WHERE emp_id = {emp_id}"
    db = get_db()
    db.execute(update_query)
    db.commit()
    return redirect(url_for("update_employee"))

#Update Employee
@app.route("/update_employee",methods=["GET","POST"])
def update_employee():
    if "loggedin" not in session:
        return render_template("login.html")
    options = ["emp_id","name","username"]
    employees = get_employees()
    if request.method == "GET":
        return render_template("edit_employess.html",\
                               options=options,employees=employees )
    search_field = request.form["options"]
    search_data = request.form["search_data"]
    query = f"select * from employees where {search_field} = '{search_data}'"
    db = get_db()
    cur = db.execute(query)
    data = cur.fetchall()
    if data:
        return render_template("edit_employess.html",options=options,\
                    condition="True",data=data,employees=employees)
    else:
        return render_template("edit_employess.html",employees=employees,options=options,condition1="False")
    

@app.route("/delete_employee_id/<emp_id>",methods=["GET"])
def delete_employee_id(emp_id):
    if "loggedin" not in session:
        return render_template("login.html")
    db=get_db()
    db.execute('delete from employees where emp_id={0}'.format(emp_id))
    db.commit()
    return redirect(url_for("delete_employee"))

#delete Employee
@app.route("/delete_employee",methods=["GET","POST"])
def delete_employee():
    if "loggedin" not in session:
        return render_template("login.html")
    options = ["emp_id","name","username"]
    employees = get_employees()
    if request.method == "GET":
        return render_template("delete_employess.html",\
                               options=options,employees=employees )
    search_field = request.form["options"]
    search_data = request.form["search_data"]
    query = f"select * from employees where {search_field} = '{search_data}'"
    db = get_db()
    cur = db.execute(query)
    data = cur.fetchall()
    if data:
        return render_template("delete_employess.html",options=options,\
                    condition="True",data=data,employees=employees)
    else:
        return render_template("delete_employess.html",employees=employees,options=options,condition1="False")
    # inp = request.get_json()
    # emp_id = inp["emp_id"]
    # 

    # return "employee deletd successfully"

###########Programs############



#add programs
@app.route("/add_program",methods=["GET","POST"])
def add_program():
    if "loggedin" not in session:
        return render_template("login.html")
    programs = get_programs()
    if request.method == "GET":
        return render_template("add_programs.html",programs=programs,conditon="False")
    program = request.form['program']
    program_release = request.form["program_release"]
    program_version = request.form["program_version"]
    programs = get_programs()
    if program and program_release and program_version:
        db = get_db()
        db.execute('insert into programs (program,program_release,program_version) values(?,?,?)',[program,program_release,program_version] )
        db.commit()
        return render_template("add_programs.html",programs=programs,condition="True",program=program,\
                           release=program_release,version=program_version)
    else:
        return render_template("add_programs.html",programs=programs,condition1="True",program=program,\
                           release=program_release,version=program_version)


@app.route("/process_update_program",methods=["POST"])
def process_update_program():
    if "loggedin" not in session:
        return render_template("login.html")
    prog_id = request.form["prog_id"]
    program_name = request.form["program_name"]
    program_release = request.form["program_release"]
    program_version = request.form["program_version"]
    
    update_query = f"UPDATE programs SET program='{program_name}',program_release='{program_release}',program_version='{program_version}' WHERE prog_id = {prog_id}"
    db = get_db()
    db.execute(update_query)
    db.commit()
    return redirect(url_for("update_program"))
    


#Update Program
@app.route("/update_program",methods=["GET","POST"])
def update_program():
    if "loggedin" not in session:
        return render_template("login.html")
    options = ["prog_id","program"]
    programs = get_programs()
    if request.method == "GET":
        return render_template("edit_programs.html",\
                               options=options,programs=programs)
    search_field = request.form["options"]
    search_data = request.form["search_data"]
    query = f"select * from programs where {search_field} = '{search_data}'"
    db = get_db()
    cur = db.execute(query)
    data = cur.fetchall()
    if data:
        return render_template("edit_programs.html",options=options,\
                    condition="True",data=data,programs=programs,name=str(data[0][1]))
    else:
        return render_template("edit_programs.html",programs=programs,options=options,condition1="False")
    return f"program data updated Successfully"

@app.route("/delete_prorgam_id/<prog_id>",methods=["GET"])
def delete_program_id(prog_id):
    if "loggedin" not in session:
        return render_template("login.html")
    db=get_db()
    db.execute('delete from programs where prog_id={0}'.format(prog_id))
    db.commit()
    return redirect(url_for("delete_program"))

#delete programs
@app.route("/delete_program",methods=["GET","POST"])
def delete_program():
    if "loggedin" not in session:
        return render_template("login.html")
    options = ["prog_id","program"]
    programs = get_programs()
    if request.method == "GET":
        return render_template("delete_programs.html",\
                               options=options,programs=programs)
    search_field = request.form["options"]
    search_data = request.form["search_data"]
    query = f"select * from programs where {search_field} = '{search_data}'"
    db = get_db()
    cur = db.execute(query)
    data = cur.fetchall()
    if data:
        return render_template("delete_programs.html",options=options,\
                    condition="True",data=data,programs=programs,name=str(data[0][1]))
    else:
        return render_template("delete_programs.html",programs=programs,options=options,condition1="False")
    # inp = request.get_json()
    # prog_id = inp["prog_id"]
    # db=get_db()
    # db.execute('delete from programs where prog_id={0}'.format(prog_id))
    # db.commit()

  
############AREAS#################
@app.route("/update_area_program/<area_id>/<prog_id>",methods=["POST"])
def update_area_program(area_id,prog_id):
    if "loggedin" not in session:
        return render_template("login.html")
    area_name = request.form["area_edit"]
    db = get_db()
    db.execute(f"update areas set area='{area_name}' where area_id='{area_id}'")
    db.commit()
    return redirect(url_for("add_update_area_program",prog_id=prog_id))



@app.route("/add_area_program/<prog_id>",methods=["POST"])
def add_area_program(prog_id):
    if "loggedin" not in session:
        return render_template("login.html")
    area_name = request.form["area_edit"]
    if area_name:
        db = get_db()
        db.execute('insert into areas (prog_id,area) values(?,?)',[prog_id,area_name] )
        db.commit()
        return redirect(url_for("add_update_area_program",prog_id=prog_id,condition1=False))
    else:
        return redirect(url_for("add_update_area_program",prog_id=prog_id,condition1=True))

    

@app.route("/add_update_area_program/<prog_id>/<condition1>",methods=["GET"])
def add_update_area_program(prog_id,condition1=False):
    if "loggedin" not in session:
        return render_template("login.html")
    if request.method == "GET":
        db = get_db()
        cur = db.execute(f"select * from areas where prog_id='{prog_id}'")
        data = cur.fetchall()
        cur1 = db.execute(f"select program from programs where prog_id='{prog_id}'")
        name = cur1.fetchall()
        program_name = None
        if name:
            program_name = name[0][0]

        return render_template("update_area_id.html",data=data,prog_id=prog_id,name=program_name,condition1=condition1)
    

#add areas
@app.route("/add_area",methods=["GET","POST"])
def add_area():
    if "loggedin" not in session:
        return render_template("login.html")
    programs = get_programs()
    if not programs:
        return render_template("no_programs.html")
    if request.method == "GET":
        return render_template('add_area.html',programs=programs)
    # inp = request.get_json()
    # prog_id = inp["prog_id"]
    # area = inp["area"]
    # db=get_db()
    # db.execute('insert into areas (prog_id,area) values(?,?)',[prog_id,area] )
    # db.commit()
    # return inp

@app.route("/delete_area/<area_id>/<prog_id>",methods=["GET","POST"])
def delete_area(area_id,prog_id):
    if "loggedin" not in session:
        return render_template("login.html")
    db= get_db()
    db.execute(f"delete from areas where area_id='{area_id}'")
    db.commit()
    return redirect(url_for("add_update_area_program",prog_id=prog_id))


######## Export Program table to XML #######################
@app.route("/export_program_xml",methods=["GET"])
def export_program_xml():
    if "loggedin" not in session:
        return render_template("login.html")
    db = get_db()
    cur = db.execute("select * from programs")
    rows = cur.fetchall()
    root = ET.Element('my_table')

    for row in rows:
        row_elem = ET.SubElement(root, 'row')
        for i, col in enumerate(row):
            col_elem = ET.SubElement(row_elem, f'col{i}')
            col_elem.text = str(col)

  
    tree = ET.ElementTree(root)
    tree.write('programs.xml', encoding='utf-8')
    return f'<h1>Downloaded Successfully</h1>'


###################### Export Employees to ASCII ############################

@app.route("/export_employee_ascii")
def export_employee_ascii():
    if "loggedin" not in session:
        return render_template("login.html")
    db = get_db()
    cur = db.execute("select * from employees")
    rows = cur.fetchall()
    with open('employees_ascii.txt', 'w') as f:
        for row in rows:
            f.write('\t'.join(str(col) for col in row) + '\n')
    return f"<h1>Downloaded Successfully"




if __name__ == "__main__":
    # port = get_free_port()
    app.run(host="localhost", port=8000, debug=True)

