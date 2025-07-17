from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import Company, Client, Invoice, LineItem
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
    return render_template('create_invoice.html', companies=companies, clients=clients)

@app.route('/company-settings')
def company_settings():
    company = Company.query.first()
    return render_template('company_settings.html', company=company)

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
        company.zip_code = request.form.get('zip_code', '')
        company.phone = request.form.get('phone', '')
        company.email = request.form.get('email', '')
        company.website = request.form.get('website', '')
        company.tax_id = request.form.get('tax_id', '')
        
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
                zip_code=request.form.get('client_zip', ''),
                phone=request.form.get('client_phone', ''),
                email=request.form.get('client_email', '')
            )
            db.session.add(client)
            db.session.flush()  # To get the client ID
        
        # Get company
        company = Company.query.first()
        if not company:
            flash('Please set up company information first', 'error')
            return redirect(url_for('company_settings'))
        
        # Generate invoice number
        last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
        invoice_number = f"INV-{(last_invoice.id + 1) if last_invoice else 1:05d}"
        
        # Create invoice
        issue_date = datetime.strptime(request.form.get('issue_date'), '%Y-%m-%d').date()
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date()
        
        invoice = Invoice(
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            notes=request.form.get('notes', ''),
            terms=request.form.get('terms', ''),
            tax_rate=Decimal(request.form.get('tax_rate', '0')),
            company_id=company.id,
            client_id=client.id
        )
        db.session.add(invoice)
        db.session.flush()  # To get the invoice ID
        
        # Add line items
        descriptions = request.form.getlist('item_description[]')
        quantities = request.form.getlist('item_quantity[]')
        rates = request.form.getlist('item_rate[]')
        
        for i in range(len(descriptions)):
            if descriptions[i].strip():  # Only add non-empty descriptions
                line_item = LineItem(
                    description=descriptions[i],
                    quantity=Decimal(quantities[i]),
                    rate=Decimal(rates[i]),
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
