# This file contains forms and their validations
from flask_wtf import FlaskForm
from wtforms.fields.core import SelectField, StringField
from wtforms.fields.simple import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.fields import html5 as h5fields
from wtforms.widgets import html5 as h5widgets

from finance.models import User

# Registration form
class RegistrationForm(FlaskForm):

    username = StringField("Username", 
                            validators=[
                                DataRequired(), 
                                Length(min=3, max=30)], 
                                render_kw={'placeholder': 'Username'})
    email = StringField(
                        "Email", 
                        validators=[
                                DataRequired(), 
                                Length(max=50),
                                Email()],
                                render_kw={'placeholder': 'Email'})
    password = PasswordField(
                        "Password", 
                        validators=[
                                DataRequired(), 
                                Length(min=8, max=50)],
                                render_kw={'placeholder': 'Password'})
    confirm_password = PasswordField(
                        "Confirm Password", 
                        validators=[
                                DataRequired(), 
                                Length(min=8, max=50),
                                EqualTo("password")],
                                render_kw={'placeholder': 'Comfirm password'})

    submit = SubmitField("Register")

    # Custom validation functions to check username and email duplication in database
    def validate_username(self, username):

        # Bring data from username field form and filter it using database
        user = User.query.filter_by(username=username.data).first()

        if user:
            raise ValidationError(f"This user '{user.username}' is exist")

    # Custom validation functions to check username and email duplication in database
    def validate_email(self, email):

        # Bring data from email field form and filter it using database
        user_email = User.query.filter_by(email=email.data).first()

        if user_email:
            raise ValidationError(f"This email '{user_email.email}' is exist")

# Log in form
class LoginForm(FlaskForm):

    username = StringField(
                            "Username", 
                            validators=[
                                DataRequired(), 
                                Length(min=1, max=30)],
                                render_kw={'placeholder': 'Username'})
    password = PasswordField(
                        "Password", 
                        validators=[
                                DataRequired(), 
                                Length(min=1, max=50)],
                                render_kw={'placeholder': 'Password'})
    login = SubmitField("Login")

# Log in form
class QuoteForm(FlaskForm):

    quote = StringField(
                        "Quote", 
                        validators=[
                            DataRequired(), 
                            Length(max=15)],
                            render_kw={'placeholder': 'Symbol'})
    query = SubmitField("Query")

# Buy form
class BuyForm(FlaskForm):

    company = StringField(
                        "Company", 
                        validators=[
                            DataRequired(), 
                            Length(max=15)],
                            render_kw={'placeholder': 'Company'})
    
    shares = h5fields.IntegerField(
                        "Share", 
                        validators=[
                            DataRequired()],
                            widget=h5widgets.NumberInput(min=1, max=999),
                            render_kw={'placeholder': 'Shares'})
    buy = SubmitField("Buy")

# Sell form
class SellForm(FlaskForm):

    symbol = SelectField(
                        "Symbol", 
                        validators=[DataRequired()], choices=[])
    
    shares = h5fields.IntegerField(
                        "Share", 
                        validators=[
                            DataRequired()],
                            widget=h5widgets.NumberInput(min=1, max=999),
                            render_kw={'placeholder': 'Shares'})
    sell = SubmitField("Sell")