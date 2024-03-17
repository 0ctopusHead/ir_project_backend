from .database import db


class Folder(db.Model):
    __tablename__ = 'folder'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)

    # Define the one-to-many relationship with Bookmark
    bookmarks = db.relationship('Bookmark', backref='folder', lazy=True)

    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name

    @property
    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'bookmarks': [bookmark.serialize for bookmark in self.bookmarks]
        }


class Bookmark(db.Model):
    __tablename__ = 'bookmark'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer)
    author_name = db.Column(db.String(255))
    image = db.Column(db.String(255))
    name = db.Column(db.String(255), nullable=False)
    recipe_category = db.Column(db.String(255))
    recipe_id = db.Column(db.Integer)
    recipe_ingredient = db.Column(db.String(255))
    recipe_instruction = db.Column(db.String(10000))
    review_count = db.Column(db.Integer)
    user_review = db.Column(db.Integer)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, user_id,folder_id, author_id, author_name, image, name, recipe_category, recipe_id, recipe_ingredient, recipe_instruction, review_count, user_review):
        self.author_id = author_id
        self.author_name = author_name
        self.image = image
        self.name = name
        self.recipe_category = recipe_category
        self.recipe_id = recipe_id
        self.recipe_ingredient = recipe_ingredient
        self.recipe_instruction = recipe_instruction
        self.review_count = review_count
        self.user_review = user_review
        self.folder_id = folder_id
        self.user_id = user_id

    @property
    def serialize(self):
        return {
            'id': self.id,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'image': self.image,
            'name': self.name,
            'recipe_category': self.recipe_category,
            'recipe_id': self.recipe_id,
            'recipe_ingredient': self.recipe_ingredient,
            'recipe_instruction': self.recipe_instruction,
            'review_count': self.review_count,
            'user_review': self.user_review,
            'folder_id': self.folder_id,
            'user_id': self.user_id
        }

    @staticmethod
    def read_list(list):
        return [m.serialize for m in list]