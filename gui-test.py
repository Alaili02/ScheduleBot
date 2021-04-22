from tkinter import *
import pymongo
myclient = pymongo.MongoClient('mongodb://localhost:27017/')
mydb = myclient['practice']
mycol = mydb["names"]

def insertToDb(_fname,_lname):
        if mycol.count_documents({ "first_name": _fname, "last_name": _lname  }) >0:
                print("user already exist ")
        else :
                mydict = { "first_name": _fname, "last_name": _lname }
                x= mycol.insert_one(mydict)
                print(f'first name is {_fname} and last name is {_lname} added to the database ')


window = Tk()

window.title("form")
window.geometry("300x200")
Label1 = Label(window, text='First name:').grid(row=0, column=0)
Fname = Entry(window)
Fname.grid(row=0, column=1)
Label1 = Label(window, text='Last name:').grid(row=1, column=0)
lname = Entry(window)
lname.grid(row=1, column=1)
button1 = Button(window, text="submit", command=lambda: insertToDb(Fname.get(), lname.get())).grid(row=2)

window.mainloop()
