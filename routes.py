from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Company, Client, Invoice, LineItem, Product, InvoiceSequence
from datetime import datetime, timedelta
from decimal import Decimal
import logging

@app.route('/')
def index():
    return redirect(url_for('create_invoice'))

@app.route('/create-invoice')
def create_invoice():
    companies = Company.query.all()
    clients = Client.query.all()
    products = Product.query.all()
    return render_template('create_invoice.html', companies=companies, clients=clients, products=products)

@app.route('/company-settings')
def company_settings():
    company = Company.query.first()
    products = Product.query.all()
    return render_template('company_settings.html', company=company, products=products)

@app.route('/invoice-history')
def invoice_history():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = Invoice.query
    
    if search:
        query = query.filter(
            db.or_(
                Invoice.invoice_number.contains(search),
                Client.name.contains(search)
            )
        ).join(Client)
    
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    
    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    # Calculate statistics
    total_invoices = Invoice.query.count()
    paid_invoices = Invoice.query.filter_by(status='paid').count()
    pending_invoices = Invoice.query.filter_by(status='pending').count()
    overdue_invoices = Invoice.query.filter_by(status='overdue').count()
    
    total_revenue = db.session.query(db.func.sum(Invoice.total)).filter_by(status='paid').scalar() or 0
    pending_amount = db.session.query(db.func.sum(Invoice.total)).filter_by(status='pending').scalar() or 0
    
    stats = {
        'total_invoices': total_invoices,
        'paid_invoices': paid_invoices,
        'pending_invoices': pending_invoices,
        'overdue_invoices': overdue_invoices,
        'total_revenue': float(total_revenue),
        'pending_amount': float(pending_amount)
    }
    
    return render_template('invoice_history.html', invoices=invoices, stats=stats, search=search, status_filter=status_filter)

@app.route('/save-company', methods=['POST'])
def save_company():
    try:
        # Get or create company (assuming single company setup)
        company = Company.query.first()
        if not company:
            company = Company()
            db.session.add(company)
        
        # Update company details
        company.name = request.form.get('name', '')
        company.address = request.form.get('address', '')
        company.city = request.form.get('city', '')
        company.state = request.form.get('state', '')
        company.pin_code = request.form.get('pin_code', '')
        company.phone = request.form.get('phone', '')
        company.email = request.form.get('email', '')
        company.website = request.form.get('website', '')
        company.gst_number = request.form.get('gst_number', '')
        company.pan_number = request.form.get('pan_number', '')
        
        db.session.commit()
        flash('Company settings saved successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving company: {e}")
        flash('Error saving company settings. Please try again.', 'error')
    
    return redirect(url_for('company_settings'))

@app.route('/save-invoice', methods=['POST'])
def save_invoice():
    try:
        # Get or create client
        client_name = request.form.get('client_name', '').strip()
        if not client_name:
            flash('Client name is required', 'error')
            return redirect(url_for('create_invoice'))
        
        client = Client.query.filter_by(name=client_name).first()
        if not client:
            client = Client(
                name=client_name,
                address=request.form.get('client_address', ''),
                city=request.form.get('client_city', ''),
                state=request.form.get('client_state', ''),
                pin_code=request.form.get('client_pin', ''),
                phone=request.form.get('client_phone', ''),
                email=request.form.get('client_email', ''),
                gst_number=request.form.get('client_gst', '')
            )
            db.session.add(client)
            db.session.flush()  # To get the client ID
        
        # Get company
        company = Company.query.first()
        if not company:
            flash('Please set up company information first', 'error')
            return redirect(url_for('company_settings'))
        
        # Generate sequential invoice number using dedicated sequence table
        current_year = datetime.now().year
        next_number = InvoiceSequence.get_next_number(current_year)
        invoice_number = f"INV-{current_year}-{next_number:05d}"
        
        # Create invoice
        issue_date = datetime.strptime(request.form.get('issue_date'), '%Y-%m-%d').date()
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
        
        invoice = Invoice(
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            notes=request.form.get('notes', ''),
            terms=request.form.get('terms', ''),
            cgst_rate=Decimal(request.form.get('cgst_rate', '9')),
            sgst_rate=Decimal(request.form.get('sgst_rate', '9')),
            igst_rate=Decimal(request.form.get('igst_rate', '0')),
            company_id=company.id,
            client_id=client.id
        )
        db.session.add(invoice)
        db.session.flush()  # To get the invoice ID
        
        # Add line items
        descriptions = request.form.getlist('item_description[]')
        quantities = request.form.getlist('item_quantity[]')
        rates = request.form.getlist('item_rate[]')
        hsn_codes = request.form.getlist('item_hsn[]')
        units = request.form.getlist('item_unit[]')
        product_ids = request.form.getlist('item_product_id[]')
        
        for i in range(len(descriptions)):
            if descriptions[i].strip():  # Only add non-empty descriptions
                line_item = LineItem(
                    description=descriptions[i],
                    quantity=Decimal(quantities[i]),
                    rate=Decimal(rates[i]),
                    hsn_code=hsn_codes[i] if i < len(hsn_codes) else '',
                    unit=units[i] if i < len(units) else 'pcs',
                    product_id=int(product_ids[i]) if i < len(product_ids) and product_ids[i] else None,
                    invoice_id=invoice.id
                )
                line_item.calculate_total()
                db.session.add(line_item)
        
        # Calculate invoice totals
        invoice.calculate_totals()
        
        db.session.commit()
        flash(f'Invoice {invoice_number} created successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error creating invoice: {e}")
        flash('Error creating invoice. Please check your input and try again.', 'error')
    
    return redirect(url_for('invoice_history'))

@app.route('/update-invoice-status/<int:invoice_id>/<status>')
def update_invoice_status(invoice_id, status):
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        invoice.status = status
        db.session.commit()
        flash(f'Invoice status updated to {status}', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating invoice status: {e}")
        flash('Error updating invoice status', 'error')
    
    return redirect(url_for('invoice_history'))

@app.route('/delete-invoice/<int:invoice_id>')
def delete_invoice(invoice_id):
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        db.session.delete(invoice)
        db.session.commit()
        flash('Invoice deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting invoice: {e}")
        flash('Error deleting invoice', 'error')
    
    return redirect(url_for('invoice_history'))

@app.route('/view-invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template('view_invoice.html', invoice=invoice)

@app.route('/add-product', methods=['POST'])
def add_product():
    try:
        company = Company.query.first()
        if not company:
            flash('Please set up company information first', 'error')
            return redirect(url_for('company_settings'))
        
        product = Product(
            name=request.form.get('product_name', ''),
            description=request.form.get('product_description', ''),
            rate=Decimal(request.form.get('product_rate', '0')),
            unit=request.form.get('product_unit', 'pcs'),
            hsn_code=request.form.get('product_hsn', ''),
            gst_rate=Decimal(request.form.get('product_gst_rate', '18')),
            company_id=company.id
        )
        
        db.session.add(product)
        db.session.commit()
        flash(f'Product "{product.name}" added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding product: {e}")
        flash('Error adding product. Please try again.', 'error')
    
    return redirect(url_for('company_settings'))

@app.route('/delete-product/<int:product_id>')
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting product: {e}")
        flash('Error deleting product', 'error')
    
    return redirect(url_for('company_settings'))

@app.route('/get-product/<int:product_id>')
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        'name': product.name,
        'description': product.description,
        'rate': float(product.rate),
        'unit': product.unit,
        'hsn_code': product.hsn_code,
        'gst_rate': float(product.gst_rate)
    })
