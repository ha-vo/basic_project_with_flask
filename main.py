from distutils.log import debug
from flask import Flask, render_template, request, redirect,url_for,flash
import os
import mysql.connector
import numpy as np

mydb = mysql.connector.connect(host='localhost', user='root', password='0807', database='BANKING')


secrect_key = os.urandom(32)

app = Flask(__name__)
app.secret_key = secrect_key

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/account', methods=['POST','GET'])
def account():
    if request.method == 'POST':
        
        user = str(request.form['user'])
        cmnd =str( request.form['cmnd'])
        day = str(request.form['day'])
        sdt = str(request.form['sdt'])
        place = str(request.form['place'])
        l = []
        for i in range(5):
            a = str(np.random.choice(range(5)))
            l.append(a)
        SoTK = ''.join(l)
        
        cursor = mydb.cursor()
        
        cursor.execute('SELECT SoTK FROM TAIKHOAN;')
        results = cursor.fetchall()
        ls = []
        for r in results:
            ls.append(r[0])
            
        while SoTK in ls:
            for i in range(5):
                a = str(np.random.choice(range(5)))
                l.append(a)
            SoTK = ''.join(l)
        
        cursor.execute('SELECT count(SoTK) FROM TAIKHOAN GROUP BY cmnd;')
        results = cursor.fetchall()
        result1 = 0
        for r in results:
            result1 += r[0]
        cursor.execute('DROP PROCEDURE IF EXISTS CHECK_INFO ;')
        cursor.execute('''
                    CREATE PROCEDURE CHECK_INFO(IN u varchar(50), c varchar(20), d varchar(20), s varchar(20), p varchar(20), tk varchar(20) )
                      BEGIN
                        IF NOT EXISTS (SELECT * FROM NGUOIDUNG,TAIKHOAN WHERE NGUOIDUNG.cmnd = c or NGUOIDUNG.TenND = u or TAIKHOAN.SoTK = tk)
                            THEN INSERT INTO NGUOIDUNG VALUES(u,c,d,p);
                                 INSERT INTO TAIKHOAN(SoTK,cmnd) VALUES(tk,c);
                                 INSERT INTO DIENTHOAI(sdt,cmnd) VALUES(s,c);
                                 COMMIT;
                        END IF;
                      END;
                       ''')
        s = 'CALL CHECK_INFO(%s,%s,%s,%s,%s,%s);'
        cursor.execute(s,(user,cmnd,day,sdt,place,SoTK))
        results = cursor.fetchall()
        cursor.execute('SELECT count(SoTK) FROM TAIKHOAN GROUP BY cmnd;')
        results = cursor.fetchall()
        result2 = 0
        for r in results:
            result2 += r[0]
        if result1 == result2:
            flash("T???o t??i kho???n th???t b???i do ng?????i d??ng ???? t???n t???i","error")
            return redirect(url_for('home'))
        mydb.commit()
        a = f'B???n v???a t??i kho???n th??nh c??ng cho ng?????i d??ng {user} v???i s??? t??i kho???n {SoTK} '
        flash(a)
        return redirect(url_for('home'))
    return render_template('account.html')

@app.route('/info')
def info():
    cursor = mydb.cursor()
    cursor.execute('''
                   select
                        NGUOIDUNG.TenND,NGUOIDUNG.cmnd,NGUOIDUNG.NgaySinh,NGUOIDUNG.quequan, TAIKHOAN.SoTK, TAIKHOAN.SoTien, DIENTHOAI.sdt, DIENTHOAI.Sotien
                   from 
                        NGUOIDUNG, TAIKHOAN, DIENTHOAI
                   where
                        NGUOIDUNG.cmnd = TAIKHOAN.cmnd and NGUOIDUNG.cmnd = DIENTHOAI.cmnd
                   ''')
    records = cursor.fetchall()   
        
    return render_template('info.html', records = records)


@app.route("/tranfers", methods = ['POST','GET'])
def tranfers():
    if request.method == 'POST':
        ac_sender = str(request.form['sender'])
        ac_receiver = str(request.form['receiver'])
        money = int(request.form['money'])
        
        cursor = mydb.cursor()
        cursor.execute('DROP FUNCTION IF EXISTS KIEM_TRA;')
        cursor.execute('''
                       CREATE FUNCTION KIEM_TRA(ac_sender varchar(20), money int, ac_receiver varchar(20)) RETURNS int
                       READS SQL DATA
                       DETERMINISTIC
                       BEGIN
                            IF EXISTS (SELECT * FROM TAIKHOAN WHERE SoTK = ac_receiver)
                                THEN
                                    IF (SELECT SoTien FROM TAIKHOAN WHERE SoTK = ac_sender) > money
                                        THEN RETURN money;
                                    ELSE 
                                        RETURN 0;
                                    END IF;
                            ELSE
                                RETURN 0;
                            END IF;
                        END
                       ''')
        cursor.execute(f'select KIEM_TRA({ac_sender},{money},{ac_receiver})')
        results = cursor.fetchall()
        for r in results:
            result = r[0]
        if result == 0:
            flash("Kh??ng th??? th???c hi???n giao d???ch v?? t??i kho???n kh??ng ????? ti???n ho???c t??i kho???n kh??ng t???n t???i","error")
            return redirect(url_for('home'))
        cursor.execute(f'select SoTien from TAIKHOAN where SoTK = {ac_sender};')
        results = cursor.fetchall() 
        for r in results:
            sender_money = int(r[0]) - result
        cursor.execute(f'select SoTien from TAIKHOAN where SoTK = {ac_receiver};')
        results = cursor.fetchall() 
        for r in results:
            receiver_money = int(r[0]) + result
        cursor.execute(f'''
                       UPDATE TAIKHOAN SET SoTien = {sender_money} WHERE  SoTK = {ac_sender}
                       ''')
        cursor.execute(f'''
                       UPDATE TAIKHOAN SET SoTien = {receiver_money} WHERE  SoTK = {ac_receiver};
                       ''')
        cursor.execute("commit;")
        mydb.commit
        flash(f"B???n v???a chuy???n th??nh c??ng s??? ti???n {result} t??? t??i kho???n {ac_sender} sang t??i kho???n {ac_receiver}","success")
        return redirect(url_for('home'))
        
    return render_template('tranfers.html')

@app.route('/recharge', methods = ['GET','POST'])
def recharge():
    if request.method == 'POST':
        ac_sender = request.form['sender']
        sdt = request.form['sdt']
        money = request.form['money']
        
        cursor = mydb.cursor()
        cursor.execute('DROP FUNCTION IF EXISTS KIEM_TRA;')
        cursor.execute('''
                       CREATE FUNCTION KIEM_TRA(ac_sender varchar(20), money int, tsdt varchar(20)) RETURNS int
                       READS SQL DATA
                       DETERMINISTIC
                       BEGIN
                            IF EXISTS ( SELECT * FROM DIENTHOAI WHERE sdt = tsdt)
                                THEN
                                    IF (SELECT SoTien FROM TAIKHOAN WHERE SoTK = ac_sender) > money
                                        THEN RETURN money;
                                    ELSE 
                                        RETURN 0;
                                    END IF;
                            ELSE
                                RETURN 0;
                            END IF;
                        END;
                       ''')
        cursor.execute(f'select KIEM_TRA({ac_sender},{money},{sdt})')
        results = cursor.fetchall()
        for r in results:
            result = r[0]
        if result == 0:
            flash("Kh??ng th??? th???c hi???n giao d???ch v?? t??i kho???n kh??ng ????? ti???n ho???c s??? t??i kho???n kh??ng t???n t???i","error")
            return redirect(url_for('home'))
        cursor.execute(f'select SoTien from TAIKHOAN where SoTK = {ac_sender}')
        results = cursor.fetchall()
        for r in results:
            sender_money = r[0] - result
        cursor.execute(f'select SoTien from DIENTHOAI where sdt = {sdt}')
        results = cursor.fetchall()
        for r in results:
            dt_money = r[0] + result
        cursor.execute('DROP TRIGGER IF EXISTS AFTER_UPDATE;')
        cursor.execute(f'''
                       CREATE TRIGGER AFTER_UPDATE AFTER UPDATE ON DIENTHOAI
                       FOR EACH ROW
                       BEGIN
                            UPDATE TAIKHOAN SET SoTien = {sender_money} WHERE SoTK = {ac_sender};
                        END
                       ''')
        cursor.execute(f'UPDATE DIENTHOAI SET SoTien = {dt_money} WHERE sdt = {sdt};')
        cursor.execute('commit;')
        mydb.commit
        flash(f'B???n v???a n???p th??nh c??ng s??? ti???n {money} v??o s??? ??i???n tho???i {sdt} t??? t??i kho???n {ac_sender}')
        return redirect(url_for('home'))
        
        
    return render_template('recharge.html')

if __name__ == "__main__":
    app.run(debug=True)
    
