import easyocr
from PIL import Image
import pandas as pd
import numpy as np
import re
import io
import mysql.connector as sql
import streamlit as st
from streamlit_option_menu import option_menu

#SQL connection to create database
    
mydb=sql.connect(host='localhost',
                user='root',
                password='',
                port='3306')
mycursor=mydb.cursor(buffered=True)
mycursor.execute('create database if not exists bizcard_data')


#page configuration
st.set_page_config(page_title="Bussiness card",  
                    layout="wide",
                    initial_sidebar_state="auto")
st.markdown('<h1 style="color:#bc6c25">BizCardX: Extracting Business Card Data with OCR</h1>', unsafe_allow_html=True)
st.divider()

#menu
with st.sidebar:
    a = option_menu(None, ["HOME","UPLOAD","MODIFY","DELETE"], 
                           icons=["house-door-fill", "cloud-upload","vector-pen","eraser"],
                           default_index=0,
                           orientation="vertical",
                           styles={"nav-link": {"font-size": "20px", "text-align": "centre", "margin": "0px", 
                                                "--hover-color": "white"},
                                   "icon": {"font-size": "20px"},
                                   "container" : {"max-width": "3000px"},
                                   "nav-link-selected": {"background-color": "black"}})


def image_to_text(path):
    image= Image.open(path)
    image_arr= np.array(image)
    reader= easyocr.Reader(['en'])
    res= reader.readtext(image_arr,detail= 0)
    return res,image


        
def data_extraction(text):
    data={"card_holdername":[],
                "Designation" :[],
                "Company_name":[],
                "Contact":[],
                "Email":[],
                "Website":[],
                "Area": [],
                "City": [],
                "State": [],
                "Pincode":[]
                }
    city = ""  
    for j, i in enumerate(text):
        
        # To get CARD HOLDER NAME
        if j == 0:
            data["card_holdername"].append(i)
        
        # To get DESIGNATION
        elif j == 1:
            data["Designation"].append(i)
        
        # To get COMPANY NAME
        elif j == len(text) - 1:
            data["Company_name"].append(i)
        
        # To get MOBILE NUMBER
        elif "-" in i:
            data["Contact"].append(i)
            if len(data["Contact"]) == 2:
                data["Contact"] = " , ".join(data["Contact"])

        # To get EMAIL ID
        elif "@" in i:
            data["Email"].append(i)
        
        # To get WEBSITE_URL
        if "www " in i.lower() or "www." in i.lower():
            data["Website"].append(i)
        elif "WWW" in i:
            data["Website"].append(text[j-1] + "." + text[j])

        # To get AREA
        if re.findall("^[0-9].+, [a-zA-Z]+", i):
            data["Area"].append(i.split(",")[0])
        elif re.findall("[0-9] [a-zA-Z]+", i):
            data["Area"].append(i)
        # To get CITY NAME
        City1 = re.findall(".+St , ([a-zA-Z]+).+", i)
        City2 = re.findall(".+St,, ([a-zA-Z]+).+", i)
        City3 = re.findall("^[E].*", i)
        if City1:
            city = City1[0]  
        elif City2:
            city = City2[0]  
        elif City3:
            city = City3[0]  
        
        # To get STATE
        state_m = re.findall("[a-zA-Z]{9} +[0-9]", i)
        if state_m:
            data["State"].append(i[:9])
        elif re.findall("^[0-9].+, ([a-zA-Z]+);", i):
            data["State"].append(i.split()[-1])
        if len(data["State"]) == 2:
            data["State"].pop(0)

        # To get PINCODE
        if len(i) >= 6 and i.isdigit():
            data["Pincode"].append(i)
        elif re.findall("[a-zA-Z]{9} +[0-9]", i):
            data["Pincode"].append(i[10:])


    data["City"].append(city)
    return data


if a=='HOME':

    col1,col2,col3=st.columns(3)    
    
    st.markdown('<h3 style="color:#9d0208">Technologies used</h3>', unsafe_allow_html=True)
    st.markdown('<h5 style="color:#a9def9">OCR, Streamlit GUI, SQL, Data Extraction</h5>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#9d0208">EasyOCR</h3>', unsafe_allow_html=True)
    st.markdown('<h5 style="color:#a9def9">EasyOCR is an open-source Optical Character Recognition (OCR) Python package that is easy to use and versatile.It is used to extract text from images or scanned documents using computers</h5>', unsafe_allow_html=True)
    st.markdown('<h3 style="color:#9d0208">Overview</h3>', unsafe_allow_html=True)
    st.markdown('<h5 style="color:#a9def9">In this streamlit web app you can upload an image of a business card and extract relevant information from it using easyOCR.This app would also allow users to save the extracted information into a database along with the uploaded business card image</h5>', unsafe_allow_html=True)


if a=='UPLOAD':
    st.markdown("""<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" rel="stylesheet">""", unsafe_allow_html=True)
    st.markdown('<h3 style="color:#38b000"><i class="fas fa-address-card"></i> Business Card</h3>', unsafe_allow_html=True)

    img = st.file_uploader(label="Upload the image", type=['png', 'jpg', 'jpeg'], label_visibility="hidden")   
 
    if img != None:
        st.image(img,width= 600)
        text_image,image= image_to_text(img)
        text_dict= data_extraction(text_image)

        if text_dict:
            st.success(":green[TEXT IS EXTRACTED SUCCESSFULLY]")
        
        df=pd.DataFrame(text_dict)
        st.dataframe(df)

        # Converting image into bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='PNG')
        imgdata_b= img_bytes.getvalue()

        #Creating dictionary
        data= {"Image":[imgdata_b]}
        df1= pd.DataFrame(data)
        df2= pd.concat([df,df1],axis=1)

        button1= st.button("Upload to Database",use_container_width= True)
        
        if button1:
            
            mydb=sql.connect(host='localhost',
                user='root',
                password='',
                port='3306',
                database='bizcard_data'
                )
            mycursor=mydb.cursor(buffered=True)
            create_table='''create table if not exists card_data (card_holdername text,
                                                         Designation text,
                                                         Company_name varchar(100),
                                                         Contact varchar(100),
                                                         Email varchar(100),
                                                         Website varchar(100),
                                                         Area varchar(50),
                                                         City varchar(50),
                                                         State varchar(50),                                                        
                                                         Pincode varchar(50),
                                                         Image LONGBLOB
                                                         )'''
            mycursor.execute(create_table)
            mydb.commit()

            for index,row in df2.iterrows():
                query='''insert into card_data 
                        (card_holdername,
                        Designation,
                        Company_name,
                        Contact,Email,
                        Website,
                        Area,
                        City,
                        State,
                        Pincode,
                        Image)
                        values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                mycursor.execute(query,tuple(row))
                mydb.commit()

                query1='''select card_holdername,Designation,Company_name,Contact,Email,Website,Area,City,State,Pincode from card_data'''
                mycursor.execute(query1)
                table = mycursor.fetchall()
                mydb.commit()

                df3=pd.DataFrame(table,columns=['card_holdername','Designation','Company_name','Contact','Email','Website','Area','City','State','Pincode'])
                st.dataframe(df3)
                st.success(":green[DATA UPLOADED SUCCESSFULLY]")

if a=="MODIFY":
    st.markdown(":red[MODIFY THE CARD DATA]")
    mydb=sql.connect(host='localhost',
                user='root',
                password='',
                port='3306',
                database='bizcard_data'
                )
    mycursor=mydb.cursor(buffered=True)
   
    mycursor.execute('''select card_holdername from card_data''' )
    tb=mycursor.fetchall()
    cards={}
    for i in tb:
        cards[i[0]]=i[0]
    options=['select card name'] + list(cards.keys())
    select_card=st.selectbox(":red[select card name]",options)

    if select_card=='select card name':
        st.warning('Card is not selected,please select the card name')
    else:
        mycursor.execute(''' select card_holdername,Designation,Company_name,Contact,Email,Website,Area,City,State,Pincode from card_data where card_holdername=%s''',(select_card,))
        tb=mycursor.fetchone()

        col1,col2=st.columns(2)
        with col1:
            a_Holdername=st.text_input("Holder_name",tb[0])
            a_Designation=st.text_input("Designation",tb[1])
            a_company_name = st.text_input("Company_Name", tb[2])
            a_contact=st.text_input("contact",tb[3])
            a_Email=st.text_input("Email",tb[4])
        
        with col2:
            a_website=st.text_input("website",tb[5])
            a_area=st.text_input("Area",tb[6])
            a_city=st.text_input("City",tb[7])
            a_state=st.text_input("State",tb[8])
            a_pincode=st.text_input("pincode",tb[9])
        

        if st.button(":red[Upload changes to database]"):
            mycursor.execute('''update card_data set card_holdername=%s,Designation=%s,Company_name=%s,Contact=%s,Email=%s,Website=%s,Area=%s,City=%s,State=%s,Pincode=%s where card_holdername=%s''',
                        (a_Holdername,a_Designation,a_company_name,a_contact,a_Email,a_website,a_area,a_city,a_state,a_pincode,select_card))
            mydb.commit()
            st.success('SUCCESSFULLY UPLOADED', icon="✅")

    if st.button(":red[View database after altered]"):
        mycursor.execute('''select card_holdername,Designation,Company_name,Contact,Email,Website,Area,City,State,Pincode from card_data''')
        table=mycursor.fetchall()
        df4=pd.DataFrame(table,columns=['card_holdername','Designation','Company_name','Contact','Email','Website','Area','City','State','Pincode'])
        st.dataframe(df4)

if a=="DELETE":
    st.markdown("### :blue[DELETE THE CARD DATA]")
    
    mydb=sql.connect(host='localhost',
                user='root',
                password='',
                port='3306',
                database='bizcard_data'
                )
    mycursor=mydb.cursor(buffered=True)
    
    col1,col2=st.columns(2)
    with col1:
        mycursor.execute('''select card_holdername from card_data''' )
        tb=mycursor.fetchall()
        cards={}
        for i in tb:
            cards[i[0]]=i[0]
        options=['None'] + list(cards.keys())
        select_card=st.selectbox("select card name",options)
        
    with col2:
        mycursor.execute('''select Designation from card_data''' )
        tb=mycursor.fetchall()
        cards={}
        for i in tb:
            cards[i[0]]=i[0]
        options=['None'] + list(cards.keys())
        select_designation=st.selectbox("select Designation name",options)
        
    col1, col2 = st.columns(2)
    with col1:
        remove = st.button(":red[Click here to delete]")
        if select_card and select_designation and remove:
            mycursor.execute(f"delete from card_data where card_holdername='{select_card}' and Designation='{select_designation}' ")
            mydb.commit()

            if remove:
                st.warning('DELETED')
        
    if st.button(":green[view the data]"):
        mycursor.execute('''select card_holdername,Designation,Company_name,Contact,Email,Website,Area,City,State,Pincode from card_data''')
        table=mycursor.fetchall()
        df5=pd.DataFrame(table,columns=['card_holder_name','Designation','Company_name','Contact','Email','Website','Area','City','State','Pin_code'])
        st.dataframe(df5)