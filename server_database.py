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

    class HistoryContacts:
        def __init__(self, from_user, to_user, date, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.date_time = date
            self.message = message

    class UsersContacts:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        self.db = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200,
                                connect_args={'check_same_thread': False})
        self.metadata = MetaData()

        clients_table = Table('AllClients', self.metadata,
                              Column('id', Integer, primary_key=True),
                              Column('name', String, unique=True),
                              Column('last_login', DateTime)
                              )

        clients_on_server = Table('Clients_online', self.metadata,
                                  Column('id', Integer, primary_key=True),
                                  Column('user', ForeignKey('AllClients.id'), unique=True),
                                  Column('ip', String),
                                  Column('port', Integer),
                                  Column('login_time', DateTime)
                                  )

        history_clients = Table('Clients_history', self.metadata,
                                Column('id', Integer, primary_key=True),
                                Column('user', ForeignKey('AllClients.id')),
                                Column('date_time', DateTime),
                                Column('ip', String),
                                Column('port', String)
                                )

        history_contacts = Table('Clients_history_contacts', self.metadata,
                                 Column('id', Integer, primary_key=True),
                                 Column('from_user', ForeignKey('AllClients.name')),
                                 Column('to_user', ForeignKey('AllClients.name')),
                                 Column('date_time', DateTime),
                                 Column('message', String),
                                 )

        contacts = Table('Contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('user', ForeignKey('AllClients.id')),
                         Column('contact', ForeignKey('AllClients.id'))
                         )

        users_history_table = Table('History', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('AllClients.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )

        self.metadata.create_all(self.db)

        mapper(self.Clients, clients_table)
        mapper(self.ClientsOnServer, clients_on_server)
        mapper(self.HistoryClients, history_clients)
        mapper(self.HistoryContacts, history_contacts)
        mapper(self.UsersContacts, contacts)
        mapper(self.UsersHistory, users_history_table)

        Session = sessionmaker(bind=self.db)
        self.session = Session()

        self.session.query(self.ClientsOnServer).delete()
        self.session.commit()

    def log_in(self, username, ip, port):
        # print(username, ip, port)
        users_query = self.session.query(self.Clients).filter_by(name=username)
        if users_query.count():
            user = users_query.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.Clients(username)
            self.session.add(user)
            self.session.commit()
            user_in_history = self.UsersHistory(user.id)
            self.session.add(user_in_history)

        new_active_user = self.ClientsOnServer(user.id, ip, port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.HistoryClients(user.id, datetime.datetime.now(), ip, port)
        self.session.add(history)

        self.session.commit()

    def log_out(self, username):

        user = self.session.query(self.Clients).filter_by(name=username).first()

        self.session.query(self.ClientsOnServer).filter_by(user=user.id).delete()

        self.session.commit()

    def process_message(self, sender, recipient):
        sender = self.session.query(self.Clients).filter_by(name=sender).first().id
        recipient = self.session.query(self.Clients).filter_by(name=recipient).first().id
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):
        user = self.session.query(self.Clients).filter_by(name=user).first()
        contact = self.session.query(self.Clients).filter_by(name=contact).first()

        if not contact or self.session.query(self.UsersContacts).filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = self.UsersContacts(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def remove_contact(self, user, contact):
        user = self.session.query(self.Users).filter_by(name=user).first()
        contact = self.session.query(self.Users).filter_by(name=contact).first()

        if not contact:
            return

        print(self.session.query(self.UsersContacts).filter(
            self.UsersContacts.user == user.id,
            self.UsersContacts.contact == contact.id
        ).delete())
        self.session.commit()

    def send_to_user(self, from_user, to_user, message):
        message = self.HistoryContacts(from_user, to_user, datetime.datetime.now(), message)
        self.session.add(message)
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

    def history_messages(self, username=None):
        query = self.session.query(self.HistoryContacts.from_user,
                                   self.HistoryContacts.to_user,
                                   self.HistoryContacts.date_time,
                                   self.HistoryContacts.message
                                   )
        if username:
            query = query.filter(self.HistoryContacts.from_user == username)
        return query.all()

    def get_contacts(self, username):
        user = self.session.query(self.Clients).filter_by(name=username).one()

        query = self.session.query(self.UsersContacts, self.Clients.name).filter_by(user=user.id). \
            join(self.Clients, self.UsersContacts.contact == self.Clients.id)

        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(
            self.Clients.name,
            self.Clients.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.Clients)
        return query.all()


if __name__ == '__main__':
    path = ''
    server_db = ServerDB(path)

    server_db.log_in('sasha', '127.0.0.1', 8080)
    server_db.log_in('pasha', '127.0.0.10', 7777)
    print(server_db.list_clients_on_server())
    server_db.log_out('sasha')
    print(server_db.list_clients_on_server())
    server_db.log_out('pasha')
    print(server_db.list_clients_on_server())
    print(server_db.history_log_in('sasha'))
    print(server_db.history_log_in())
