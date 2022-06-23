#!/usr/bin/env python3
"""
The following code should import a CSV file into a postgres database. 
It's very much a proof of concept. There would be changes necessary to make it a robust Lambda function.
For now, it is working against local services/CSV files.
Ultimately it's workflow would be something like this:
1. Get the csv file from S3
2. Marshall the data into classes using the partner mapping information from DynamoDB
4. Write the classes to a postgres database
"""

from unicodedata import decimal
import sqlalchemy
from sqlalchemy.orm import declarative_base, Session
import argparse
import csv
import pathlib
import localstack_client.session as boto3

engine = sqlalchemy.create_engine(
    "postgresql://postgres:example@localhost:5432/postgres"
)
endpoint_url = "http://localhost.localstack.cloud:4566"
Base = declarative_base()


class Expense(Base):
    __tablename__ = "expense_lines"
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    amount = sqlalchemy.Column(sqlalchemy.Float)
    description = sqlalchemy.Column(sqlalchemy.String)
    date = sqlalchemy.Column(sqlalchemy.Date)
    type = sqlalchemy.Column(sqlalchemy.String)
    user_ssn = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey("user_data.ssn")
    )
    partner_id = sqlalchemy.Column(sqlalchemy.Integer)


class User(Base):
    __tablename__ = "user_data"
    ssn = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    firstname = sqlalchemy.Column(sqlalchemy.String)
    lastname = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String)

    def __eq__(self, other: object) -> bool:
        if other is not None:
            return self.ssn == other.ssn
        else:
            return False

    def __hash__(self) -> int:
        return hash(self.ssn)


def get_partner_information(partner_id: int) -> dict:
    """
    This function is used to get partner data from a DynamoDB table.
    """
    response = (
        boto3.resource("dynamodb")
        .Table("partner_info")
        .get_item(Key={"partner_id": partner_id})["Item"]
    )
    response["mapping"]["partner_id"] = partner_id
    return replace_decimal_integer(response.get("mapping"))


def replace_decimal_integer(dictionary: dict) -> dict:
    """
    This function will replace the decimal integer values with integers.
    """
    for key, value in dictionary.items():
        dictionary[key] = int(value) if value != None else None
    return dictionary


def marshall_user(user: list, partner_info: dict) -> User:
    """
    This function will marshall the user data into a User object.
    """
    firstname = None
    lastname = None
    if partner_info.get("firstname") == None:
        firstname = user[partner_info.get("lastname")].split(" ")[0]
        lastname = user[partner_info.get("lastname")].split(" ")[1]
    else:
        firstname = user[partner_info.get("firstname")]
        lastname = user[partner_info.get("lastname")]
    return User(
        firstname=firstname,
        lastname=lastname,
        email=user[partner_info.get("email")]
        if partner_info.get("email") != None
        else None,
        ssn=user[partner_info.get("ssn")] if partner_info.get("ssn") != None else None,
    )


def marshall_expense(expense: list, partner_info: dict) -> Expense:
    """
    This function will marshall the expense data into an Expense object.
    """
    return Expense(
        amount=expense[partner_info.get("amount")]
        if partner_info.get("amount") != None
        else None,
        description=expense[partner_info.get("description")]
        if partner_info.get("description") != None
        else None,
        date=expense[partner_info.get("date")]
        if partner_info.get("date") != None
        else None,
        type=expense[partner_info.get("type")]
        if partner_info.get("type") != None
        else None,
        partner_id=partner_info.get("partner_id")
        if partner_info.get("partner_id") != None
        else None,
        user_ssn=expense[partner_info.get("ssn")]
        if partner_info.get("ssn") != None
        else None,
    )


def get_users_expenses(csv_file_path: pathlib.Path, partner_id: int) -> list:
    """
    This function will return a list of objects that can be written to a postgres database.
    """
    users = []
    expenses = []
    partner_info = get_partner_information(partner_id)
    with open(csv_file_path, "r") as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=",")
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                users.append(marshall_user(row, partner_info))
                expenses.append(marshall_expense(row, partner_info))
                line_count += 1
    users = list(set(users))
    return users, expenses


def save_to_db(users: list, expenses: list) -> None:
    """
    This function will save the users and expenses to the postgres database.
    """
    session = Session(engine)
    for user in users:
        if session.query(User).filter(User.ssn == user.ssn).first() == None:
            session.add(user)
            session.flush()
    for expense in expenses:
        session.add(expense)
        session.flush()
    session.commit()


def main(csv_file_path: pathlib.Path, partner_id: int) -> None:
    users, expenses = get_users_expenses(csv_file_path, partner_id)
    save_to_db(users, expenses)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(dest="csv_file_path", help="The path to the csv file")
    parser.add_argument(dest="partner_id", help="The ID of the partner", type=int)
    args = parser.parse_args()
    main(pathlib.Path(args.csv_file_path), args.partner_id)
