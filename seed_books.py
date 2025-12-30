import random
import sys
import os

# Add the admin_panel directory to the path so we can import db
sys.path.append(os.path.join(os.path.dirname(__file__), 'admin_panel'))
from db import add_book_bulk

books_data = [
    ("9780451524935", "1984", "George Orwell", "Fiction"),
    ("9780061120084", "To Kill a Mockingbird", "Harper Lee", "Fiction"),
    ("9780743273565", "The Great Gatsby", "F. Scott Fitzgerald", "Fiction"),
    ("9780316769174", "The Catcher in the Rye", "J.D. Salinger", "Fiction"),
    ("9780141439518", "Pride and Prejudice", "Jane Austen", "Fiction"),
    ("9780544003415", "The Lord of the Rings", "J.R.R. Tolkien", "Fiction"),
    ("9780618260300", "The Hobbit", "J.R.R. Tolkien", "Fiction"),
    ("9780345339683", "The Fellowship of the Ring", "J.R.R. Tolkien", "Fiction"),
    ("9780439023528", "The Hunger Games", "Suzanne Collins", "Fiction"),
    ("9780439064873", "Harry Potter and the Chamber of Secrets", "J.K. Rowling", "Fiction"),
    ("9780439136365", "Harry Potter and the Prisoner of Azkaban", "J.K. Rowling", "Fiction"),
    ("9780439139601", "Harry Potter and the Goblet of Fire", "J.K. Rowling", "Fiction"),
    ("9780142437230", "Don Quixote", "Miguel de Cervantes", "Literature"),
    ("9780140449136", "The Odyssey", "Homer", "History"),
    ("9780141439587", "Moby Dick", "Herman Melville", "Literature"),
    ("9780141439600", "Great Expectations", "Charles Dickens", "Literature"),
    ("9780140449266", "Crime and Punishment", "Fyodor Dostoevsky", "Literature"),
    ("9780307474278", "The Da Vinci Code", "Dan Brown", "Fiction"),
    ("9781400079179", "The Alchemist", "Paulo Coelho", "Fiction"),
    ("9780375842207", "The Book Thief", "Markus Zusak", "Fiction"),
    ("9780143127741", "The Martian", "Andy Weir", "Science"),
    ("9780553103540", "A Game of Thrones", "George R.R. Martin", "Fiction"),
    ("9780743247542", "The Kite Runner", "Khaled Hosseini", "Fiction"),
    ("9781101904220", "Dark Matter", "Blake Crouch", "Science"),
    ("9780385504200", "The Da Vinci Code", "Dan Brown", "Fiction"),
    ("9780593135204", "Project Hail Mary", "Andy Weir", "Science"),
    ("9780316405287", "Ready Player One", "Ernest Cline", "Technology"),
    ("9780553213119", "Moby-Dick", "Herman Melville", "Literature"),
    ("9780140177398", "Of Mice and Men", "John Steinbeck", "Literature"),
    ("9780451526342", "Animal Farm", "George Orwell", "Fiction"),
    ("9780140283334", "The Grapes of Wrath", "John Steinbeck", "Literature"),
    ("9780743273565", "The Great Gatsby", "F. Scott Fitzgerald", "Literature"),
    ("9780141439556", "Wuthering Heights", "Emily Brontë", "Literature"),
    ("9780141439600", "Great Expectations", "Charles Dickens", "Literature"),
    ("9780486280615", "The Adventures of Huckleberry Finn", "Mark Twain", "Literature"),
    ("9780140449334", "The Brothers Karamazov", "Fyodor Dostoevsky", "Literature"),
    ("9780679720201", "The Stranger", "Albert Camus", "Literature"),
    ("9780141439471", "Frankenstein", "Mary Shelley", "Fiction"),
    ("9780141439594", "Jane Eyre", "Charlotte Brontë", "Literature"),
    ("9780140441000", "Madame Bovary", "Gustave Flaubert", "Literature"),
    ("9780140447934", "The Divine Comedy", "Dante Alighieri", "History"),
    ("9780140447699", "War and Peace", "Leo Tolstoy", "History"),
    ("9780140444308", "Anna Karenina", "Leo Tolstoy", "Literature"),
    ("9780140449266", "Crime and Punishment", "Fyodor Dostoevsky", "Literature"),
    ("9781501173219", "Fear and Loathing in Las Vegas", "Hunter S. Thompson", "Non-Fiction"),
    ("9780307277671", "The Road", "Cormac McCarthy", "Fiction"),
    ("9780062316097", "Sapiens", "Yuval Noah Harari", "Non-Fiction"),
    ("9781101904220", "Dark Matter", "Blake Crouch", "Science"),
    ("9780385504200", "The Da Vinci Code", "Dan Brown", "Fiction"),
    ("9780143127741", "The Martian", "Andy Weir", "Science")
]

def seed_books():
    print(f"Starting to seed {len(books_data)} real books...")
    for isbn, title, author, category in books_data:
        quantity = random.randint(7, 16)
        try:
            success, barcodes = add_book_bulk(isbn, title, author, category, quantity)
            if success:
                print(f"Successfully added '{title}' with {quantity} copies.")
            else:
                print(f"Failed to add '{title}'.")
        except Exception as e:
            print(f"Error adding '{title}': {e}")

if __name__ == "__main__":
    seed_books()
    print("\nSeeding complete! Check your Admin Panel Dashboard.")
