from app import db
from datetime import datetime
from sqlalchemy import func

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    pin_code = db.Column(db.String(10))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    gst_number = db.Column(db.String(50))
    pan_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    invoices = db.relationship('Invoice', backref='company', lazy=True)
    products = db.relationship('Product', backref='company', lazy=True)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    pin_code = db.Column(db.String(10))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    gst_number = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    invoices = db.relationship('Invoice', backref='client', lazy=True)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue
    notes = db.Column(db.Text)
    terms = db.Column(db.Text)
    
    # Financial fields
    subtotal = db.Column(db.Numeric(10, 2), default=0)
    cgst_rate = db.Column(db.Numeric(5, 2), default=9)  # Central GST
    sgst_rate = db.Column(db.Numeric(5, 2), default=9)  # State GST
    igst_rate = db.Column(db.Numeric(5, 2), default=0)  # Integrated GST
    cgst_amount = db.Column(db.Numeric(10, 2), default=0)
    sgst_amount = db.Column(db.Numeric(10, 2), default=0)
    igst_amount = db.Column(db.Numeric(10, 2), default=0)
    total_gst = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), default=0)
    
    # Foreign keys
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    line_items = db.relationship('LineItem', backref='invoice', lazy=True, cascade='all, delete-orphan')
    
    def calculate_totals(self):
        """Calculate invoice totals based on line items with GST"""
        self.subtotal = sum(item.total for item in self.line_items)
        
        # Calculate GST amounts
        if self.igst_rate > 0:
            # Inter-state transaction - use IGST only
            self.igst_amount = self.subtotal * (self.igst_rate / 100)
            self.cgst_amount = 0
            self.sgst_amount = 0
        else:
            # Intra-state transaction - use CGST + SGST
            self.cgst_amount = self.subtotal * (self.cgst_rate / 100)
            self.sgst_amount = self.subtotal * (self.sgst_rate / 100)
            self.igst_amount = 0
        
        self.total_gst = self.cgst_amount + self.sgst_amount + self.igst_amount
        self.total = self.subtotal + self.total_gst

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    rate = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(50), default='pcs')  # units like pcs, kg, ltr, etc.
    hsn_code = db.Column(db.String(20))  # HSN/SAC code for GST
    gst_rate = db.Column(db.Numeric(5, 2), default=18)  # GST rate for this product
    
    # Foreign key
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    rate = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    hsn_code = db.Column(db.String(20))
    unit = db.Column(db.String(50), default='pcs')
    
    # Foreign keys
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    
    def calculate_total(self):
        """Calculate line item total"""
        self.total = self.quantity * self.rate
