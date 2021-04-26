from tkinter import *
import time
window = Tk()
window.title("form")
window.geometry("800x300")
import pymongo
def insertToDb(_fname,_lname,window,listbox,col):
      label2_txt=""
      Label2 = Label(window, text=label2_txt)  
      if mycol.count_documents({ "first_name": _fname, "last_name": _lname  }) >0:
              Label2['text']="user already exist"
              Label2.grid (row=4,column=1)
                
      else :
                mydict = { "first_name": _fname, "last_name": _lname }
                x= mycol.insert_one(mydict)
                Label2['text']="added to the database"
                Label2.grid (row=4,column=1)
                print(f' {_fname}  {_lname} added to the database ')
                printNames(listbox,col)
def printNames(listbox1,collection):
        for x in collection.find():
                listbox1.insert(0,x)
       
try: 
        myclient = pymongo.MongoClient('mongodb://localhost:27017/',serverSelectionTimeoutMS = 2000)
        myclient.server_info()
        mydb = myclient['practice']
        mycol = mydb["names"]    
               
        Label1 = Label(window, text='First name:').grid(row=0, column=0)
        Fname = Entry(window)
        Fname.grid(row=0, column=1)
        Label1 = Label(window, text='Last name:').grid(row=1, column=0)
        lname = Entry(window)
        lname.grid(row=1, column=1)
        listbox = Listbox(window,height = 10,width =80)
        listbox.place(relx=0.3, rely=0.1)
        printNames(listbox,mycol) 
        button1 = Button(window, text="submit", command=lambda: insertToDb(Fname.get(), lname.get(),window,listbox,mycol)).place(relx=0.4, rely=0.8, anchor=CENTER)     
        button1 = Button(window, text="exit",fg='red', command=window.destroy).place(relx=0.6, rely=0.8, anchor=CENTER)
        window.mainloop()


except:
        Label1 = Label(window, text='connection error please connect to the server').place(relx=0.5, rely=0.2, anchor=CENTER)
        button1 = Button(window, text="exit",fg='red', command=window.destroy).place(relx=0.5, rely=0.5, anchor=CENTER)
        window.mainloop()
        







