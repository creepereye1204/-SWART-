from flask import Flask, request, render_template, redirect,url_for,session,jsonify, send_file
from flask_cors import CORS
from flask_socketio import join_room, leave_room, send, SocketIO



import random
from string import ascii_uppercase
import binascii
import json
import cert, model
import sys
import hashlib
import os
import datetime
import imghdr
import shutil
import socket
from flask_session import Session

import uuid
#찐 알파
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SECRET_KEY"] = "hjhjsdahhds"
CORS(app)
Session(app)
socketio = SocketIO(app, cors_allowed_origins="*")








rooms = {}
def generate_unique_code(length):
  while True:
    code = ""
    for _ in range(length):
      code += random.choice(ascii_uppercase)

    if code not in rooms:
      break

  return code


@app.route("/chat", methods=["POST", "GET"])
def chat():
  if 'email' not in session:
    return session_guard()
  session.pop('room', None)
  session.pop('name', None)
  if request.method == "POST":
    name = request.form.get("name")
    code = request.form.get("code")
    join = request.form.get("join", False)
    create = request.form.get("create", False)

    if not name:
      return render_template("home.html",
                             error="Please enter a name.",
                             code=code,
                             name=name)

    if join != False and not code:
      return render_template("home.html",
                             error="Please enter a room code.",
                             code=code,
                             name=name)

    room = code
    if create != False:
      room = generate_unique_code(4)
      rooms[room] = {"members": 0, "messages": []}
    elif code not in rooms:
      return render_template("home.html",
                             error="Room does not exist.",
                             code=code,
                             name=name)

    session["room"] = room
    session["name"] = name
    return redirect(url_for("room"))

  return render_template("home.html")


@app.route("/chat/room")
def room():
  if 'email' not in session:
    return session_guard()
  room = session.get("room")
  if room is None or session.get("name") is None or room not in rooms:
    return redirect(url_for("home"))

  return render_template("room.html",
                         code=room,
                         messages=rooms[room]["messages"])


@socketio.on("message")
def message(data):
  if 'email' not in session:
        return session_guard()
  room = session.get("room")
  if room not in rooms:
    return

  content = {"name": session.get("name"), "message": data["data"]}
  send(content, to=room)
  rooms[room]["messages"].append(content)
  print(f"{session.get('name')} said: {data['data']}")


@socketio.on("connect")
def connect(auth):
  if 'email' not in session:
    return session_guard()
  room = session.get("room")
  name = session.get("name")
  if not room or not name:
    return
  if room not in rooms:
    leave_room(room)
    return

  join_room(room)
  send({"name": name, "message": "has entered the room"}, to=room)
  rooms[room]["members"] += 1
  print(f"{name} joined room {room}")


@socketio.on("disconnect")
def disconnect():
  if 'email' not in session:
        return session_guard()
  room = session.get("room")
  name = session.get("name")
  leave_room(room)

  if room in rooms:
    rooms[room]["members"] -= 1
    if rooms[room]["members"] <= 0:
      del rooms[room]

  send({"name": name, "message": "has left the room"}, to=room)
  print(f"{name} has left the room {room}")



def session_guard():
    return """
        <script>
            alert('로그인해주세요');
            window.location.href='/';
        </script>
    """
    
        

# 랜덤 UUID 생성
def remove(paths):
    for path in paths:
        for key,value in path.items():
            os.remove(os.path.join('static',value))
        
def save(path,text):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(str(text))

def read(path):
    txt_file = open(path, 'r')
    text=txt_file.read()
    txt_file.close()
    return text

def view():
    sql=f"""
      SELECT * FROM ARTICLE
      """
    return model.conn(sql)

def board_comment(article_id):
    comments=[]
    sql=f"""
      SELECT * FROM COMMENTS WHERE ARTICLE_ID={article_id}
      """
    paths=model.conn(sql)
    for path in paths:
        
        comments.append(read("static/"+path['COMMENTS']))
    
    return comments


def board(article_id):
    sql=f"""
      SELECT * FROM ARTICLE WHERE ARTICLE_ID={article_id}
      """

    return model.conn(sql)[0]

def insert(article_id,thumbnail_path,email='sCASASC',title='s',content='s'):
    print(thumbnail_path)
    sql=f"""
      INSERT INTO ARTICLE (article_id, email, thumbnail_path, title, content, recorded_time)
      VALUES ({article_id},'{email}', '{thumbnail_path}', '{title}', '{content}', SYSDATE)
      """
    model.conn(sql)

    
@app.route('/upload', methods=['POST'])
def upload():
    if 'email' not in session:
        return session_guard()
    data = request.get_json()
    filename = data['filename']
    hex_string = data['hexString']

    # 16진수 문자열을 바이트로 변환합니다.
    bytes = binascii.unhexlify(hex_string)

    # 바이트를 파일로 저장합니다.
    # 'static/upload' 디렉토리에 저장하도록 수정했습니다.
    os.makedirs('static/upload', exist_ok=True)
    with open(os.path.join('static', 'upload', filename), 'wb') as f:
        f.write(bytes)

    # 파일에 대한 URL을 생성합니다.
    # URL도 'static/upload' 디렉토리를 가리키도록 수정했습니다.
    url =  "/download/"+filename

    # URL을 클라이언트에게 전달합니다.
    return url

@app.route('/download/<filename>')
def download(filename):
    if 'email' not in session:
        return session_guard()
    path='static/upload/' +filename
    return send_file(path, as_attachment=True)







@app.route("/")
def root():
    return render_template("login/index.html")





@app.route("/login")
def login():
    
    code = request.args.get('code')
    info = cert.cert(code)
    query = "select * from CLIENT where email='%s'" % info['email']
    user = model.conn(query=query)
    
    if not user:
        sql=f"""
            INSERT INTO CLIENT (EMAIL,NAME) VALUES ('{info['email']}','{info['birthday']}')
        """
        model.conn(sql)
    session['email']=info['email']
    
    
    return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('email', None)
    
    return redirect(url_for('root'))

@app.route("/home")
def home():
    if 'email' not in session:
        return session_guard()
    
    
    card_list=view()
    titles=[]
    for card in card_list:
        path=os.path.join('static',card['TITLE'])
        titles.append(read(path))
    card_list=zip(card_list,titles)
    
    
    
    return render_template("/home/index.html",cards=card_list)

@app.route("/home/<article_id>", methods=['GET', 'POST'])
def article(article_id):
    if 'email' not in session:
        return session_guard()
    
    card=board(article_id)
    coments=board_comment(article_id)

    content_path=os.path.join('static',card['CONTENT'])
    title_path=os.path.join('static',card['TITLE'])
    
    # 파일 열기
    content_file = open(content_path, 'r')
    title_file = open(title_path, 'r')
    # 파일 읽기
    content =  content_file.read()
    title = title_file.read()
    # 파일 닫기
    content_file.close()
    title_file.close()
    comments=board_comment(article_id)
    
    return render_template("/article/index.html",card =card,content=content,title=title,article_id=article_id,comments=comments,author=True)



@app.route("/home/<article_id>/modify", methods=['GET', 'POST'])
def modify(article_id):
    if 'email' not in session:
        return session_guard()
    if request.method=="GET":
        #대충 세션확인
        #나중에
        article=board(article_id)
        title_path=article['TITLE']
        content_path=article['CONTENT']
        thumbnail_path=article['THUMBNAIL_PATH']
        title=read(os.path.join('static',title_path))
        content=read(os.path.join('static',content_path))
        return render_template('modify/index.html',title=title,content=content,thumbnail_path=thumbnail_path,article_id=article_id)
    else:
        file = request.files['thumbnail']
        title = request.form['title']
        content = request.form['content']
        print(article_id)
        article=board(article_id)
        title_path=os.path.join('static',article['TITLE'])
        content_path=os.path.join('static',article['CONTENT'])
        thumbnail_path=os.path.join('static',article['THUMBNAIL_PATH'])
        path=""
        if 'changeThumbnail' in request.form and request.form['changeThumbnail']:
            os.remove(thumbnail_path)
            
            path=os.path.join('thumbnail',str(uuid.uuid4()))
            if len(file.filename)>0: 
                _, ext = os.path.splitext(file.filename)
                path+=ext
                file.save(os.path.join('static',path))
            else:
                path+='.png'
                shutil.copy2('static/thumbnail/default.png',os.path.join('static',path))
            sql=f"""
                UPDATE ARTICLE SET THUMBNAIL_PATH='{path}' 
                WHERE ARTICLE_ID={article_id}
            """
            model.conn(sql)
        save(title_path,title)
        save(content_path,content)
        return redirect(url_for('article',article_id=article_id))

@app.route("/home/<article_id>/delete", methods=['GET', 'POST'])
def delete(article_id):
    if 'email' not in session:
        return session_guard()
    sql=f"""
        SELECT THUMBNAIL_PATH,TITLE,CONTENT FROM ARTICLE WHERE ARTICLE_ID={article_id}
    """
    article=model.conn(sql)
    
    sql=f"""
        SELECT COMMENTS FROM COMMENTS WHERE ARTICLE_ID={article_id}
    """
    comment=model.conn(sql)
    
    remove(article)
    remove(comment)
    
    
    sql=f"""
        DELETE FROM ARTICLE WHERE ARTICLE_ID={article_id}
    """
    model.conn(sql)
    f"""
        DELETE FROM COMMENTS WHERE ARTICLE_ID={article_id}
    """
    model.conn(sql)
    f"""
        COMMIT
    """
    model.conn(sql)
    return redirect(url_for('home'))

@app.route("/home/<article_id>/comment", methods=['GET', 'POST'])
def comment(article_id):
    if 'email' not in session:
        return session_guard()
    email="sample"
    if request.method=='POST':
        comment=request.form['comment']
        txt_name=str(uuid.uuid4())
        txt='comment/'+txt_name+'.txt'
        save(os.path.join('static',txt),comment)
        sql=f"""
              INSERT INTO COMMENTS (article_id, email,comments,recorded_time)
              VALUES ({article_id},'{email}', '{txt}', SYSDATE)
             """
        model.conn(sql)
        return redirect(url_for('article',article_id=article_id))
            
            
            
    



@app.route("/home/write", methods=['GET', 'POST'])
def write():
    if 'email' not in session:
        return session_guard()
    print(session.get('key', 'not set'))
    if request.method=='GET':
        return render_template("/write/index.html")
    else:

        title = request.form['title']
        content = request.form['content']

        file = request.files['thumbnail']
        filename=file.filename
        file_format = os.path.splitext(filename)[-1].lower()
        path='thumbnail/default.png'
        num=0
        
        with open('index.txt', 'r') as f:
            num = int(f.read())
        with open('index.txt', 'w') as f:
            f.write(str(num+1))

        name, ext = os.path.splitext(filename)

        filename=str(uuid.uuid4())+ext

        path=f'static/thumbnail/{filename}'

        if file_format in ['.jpg', '.jpeg', '.png', '.gif']:
            file.save(path)
            path=f'thumbnail/{filename}'
        else:
            shutil.copy2('static/thumbnail/default.png',path+'.png')
            path=f'thumbnail/{filename}'+'.png'
        print(path)
            
            
            
            

        
        txt_name=str(uuid.uuid4())
        html='static/content/'+txt_name+'.txt'
        txt='static/title/'+txt_name+'.txt'


        with open(txt, 'w', encoding='utf-8') as f:
            f.write(str(title))
        with open(html, 'w', encoding='utf-8') as f:
            f.write(str(content))

        c='content/'+txt_name+'.txt'
        t='title/'+txt_name+'.txt'

        insert(article_id=num,thumbnail_path=path,email='sCASASC',title=t,content=c)

        return redirect(url_for('home'))


if __name__ == "__main__":
    socketio.run(app, '0.0.0.0', debug=True)
    
