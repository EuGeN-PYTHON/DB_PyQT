from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class ServerDB:
    class Clients:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None

    class ClientsOnServer:
        def __init__(self, user_id, ip, port, login_time):
            self.user = user_id
            self.ip = ip
            self.port = port
            self.login_time = login_time
            self.id = None

    class HistoryClients:
        def __init__(self, user, date, ip, port):
            self.id = None
            self.user = user
            self.date_time = date
            self.ip = ip
            self.port = port

    def __init__(self):
        self.db = create_engine('sqlite:///db_server.db3', echo=False, pool_recycle=7200)
        self.metadata = MetaData()

        clients_table = Table('Clients', self.metadata,
                              Column('id', Integer, primary_key=True),
                              Column('name', String, unique=True),
                              Column('last_login', DateTime)
                              )

        clients_on_server = Table('Clients_online', self.metadata,
                                  Column('id', Integer, primary_key=True),
                                  Column('user', ForeignKey('Clients.id'), unique=True),
                                  Column('ip', String),
                                  Column('port', Integer),
                                  Column('login_time', DateTime)
                                  )

        history_clients = Table('Clients_history', self.metadata,
                                Column('id', Integer, primary_key=True),
                                Column('user', ForeignKey('Clients.id')),
                                Column('date_time', DateTime),
                                Column('ip', String),
                                Column('port', String)
                                )

        self.metadata.create_all(self.db)

        mapper(self.Clients, clients_table)
        mapper(self.ClientsOnServer, clients_on_server)
        mapper(self.HistoryClients, history_clients)

        Session = sessionmaker(bind=self.db)
        self.session = Session()

        self.session.query(self.ClientsOnServer).delete()
        self.session.commit()

    def log_in(self, username, ip, port):
        print(username, ip, port)
        users_query = self.session.query(self.Clients).filter_by(name=username)
        if users_query.count():
            user = users_query.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.Clients(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ClientsOnServer(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.HistoryClients(user.id, datetime.datetime.now(), ip, port)
        self.session.add(history)

        self.session.commit()

    def log_out(self, username):

        user = self.session.query(self.Clients).filter_by(name=username).first()

        self.session.query(self.ClientsOnServer).filter_by(user=user.id).delete()

        self.session.commit()

    def list_clients(self):
        query = self.session.query(
            self.Clients.name,
            self.Clients.last_login,
        )
        return query.all()

    def list_clients_on_server(self):
        query = self.session.query(
            self.Clients.name,
            self.ClientsOnServer.ip,
            self.ClientsOnServer.port,
            self.ClientsOnServer.login_time
            ).join(self.Clients)
        return query.all()

    def history_log_in(self, username=None):
        query = self.session.query(self.Clients.name,
                                   self.HistoryClients.date_time,
                                   self.HistoryClients.ip,
                                   self.HistoryClients.port
                                   ).join(self.Clients)
        if username:
            query = query.filter(self.Clients.name == username)
        return query.all()

if __name__ == '__main__':

    server_db = ServerDB()

    server_db.log_in('sasha', '127.0.0.1', 8080)
    server_db.log_in('pasha', '127.0.0.10', 7777)
    print(server_db.list_clients_on_server())
    server_db.log_out('sasha')
    print(server_db.list_clients_on_server())
    server_db.log_out('pasha')
    print(server_db.list_clients_on_server())
    print(server_db.history_log_in('sasha'))
    print(server_db.history_log_in())