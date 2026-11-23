# Five titles and lab prices follow the course Chapter 2 example.
BOOKS = [
    ('The Pragmatic Programmer','David Thomas & Andrew Hunt',2019,'Software Engineering',49.99,'978-0135957059',['programming','career','best-practices'],'Addison-Wesley','Boston'),
    ('Designing Data-Intensive Applications','Martin Kleppmann',2017,'Databases',45.99,'978-1449373320',['databases','distributed-systems','architecture'],"O'Reilly Media",'Sebastopol'),
    ('Deep Learning','Ian Goodfellow, Yoshua Bengio, Aaron Courville',2016,'Machine Learning',72.00,'978-0262035613',['AI','neural-networks','theory'],'MIT Press','Cambridge'),
    ('Clean Code','Robert C. Martin',2008,'Software Engineering',39.99,'978-0132350884',['programming','clean-code','refactoring'],'Prentice Hall','Upper Saddle River'),
    ('Hands-On Machine Learning','Aurelien Geron',2022,'Machine Learning',59.99,'978-1098125974',['AI','scikit-learn','tensorflow','practical'],"O'Reilly Media",'Sebastopol')]

def seed(col):
    col.delete_many({})
    docs = [dict(title=t,author=a,year=y,genre=g,price=p,isbn=i,tags=tags,
                 publisher={'name':pub,'location':loc})
            for t,a,y,g,p,i,tags,pub,loc in BOOKS]
    col.insert_many(docs)
    assert col.count_documents({}) == 5
