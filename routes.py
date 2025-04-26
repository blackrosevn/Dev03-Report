from flask import render_template, redirect, url_for, flash, request, session, jsonify, g, send_file
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse
from app import app, db
from models import User, Role, Organization, ReportTemplate, ReportAssignment, ReportSubmission, Settings, ReportStatus, ReportFrequency, AuditLog, EmailLog
from forms import LoginForm, RegisterForm, UserForm, OrganizationForm, ReportTemplateForm, ReportAssignmentForm, ReportSubmissionForm, SettingsForm, ChangeLanguageForm, ChangePasswordForm
from utils import send_email, save_excel_file, generate_excel, create_user, log_action
import os
import json
from datetime import datetime, timedelta
import pandas as pd
from config import SAMPLE_REPORT_TEMPLATES, DEFAULT_SETTINGS

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data) or not user.is_active:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Log action
        log_action(user.id, 'login', 'User logged in', request.remote_addr)

        # Set session language
        session['language'] = user.language

        next_page = request.args.get('next')
        if not next_page or urlparse(next_page).netloc != '':
            next_page = url_for('dashboard')

        return redirect(next_page)

    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    log_action(current_user.id, 'logout', 'User logged out', request.remote_addr)
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    # Only admin can create new users
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    form = RegisterForm()
    form.role.choices = [(r.id, r.description) for r in Role.query.all()]
    form.organization.choices = [(o.id, o.name) for o in Organization.query.filter_by(is_active=True).all()]

    if form.validate_on_submit():
        user = create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            fullname=form.fullname.data,
            role_id=form.role.data,
            organization_id=form.organization.data
        )

        flash('User registered successfully!', 'success')
        log_action(current_user.id, 'create_user', f'Created user: {user.username}', request.remote_addr)
        return redirect(url_for('user_management'))

    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    # Stats for admins and department users
    if current_user.is_admin() or current_user.is_department():
        total_reports = ReportAssignment.query.count()
        pending_reports = ReportAssignment.query.filter_by(status=ReportStatus.PENDING).count()
        submitted_reports = ReportAssignment.query.filter_by(status=ReportStatus.SUBMITTED).count()
        overdue_reports = ReportAssignment.query.filter_by(status=ReportStatus.OVERDUE).count()

        # Recent submissions
        recent_submissions = db.session.query(
            ReportSubmission, User, Organization, ReportTemplate
        ).join(
            ReportAssignment, ReportSubmission.report_assignment_id == ReportAssignment.id
        ).join(
            User, ReportSubmission.submitted_by == User.id
        ).join(
            Organization, User.organization_id == Organization.id
        ).join(
            ReportTemplate, ReportAssignment.report_template_id == ReportTemplate.id
        ).order_by(
            ReportSubmission.submitted_at.desc()
        ).limit(10).all()

        # Upcoming deadlines
        upcoming_deadlines = db.session.query(
            ReportAssignment, Organization, ReportTemplate
        ).join(
            Organization, ReportAssignment.organization_id == Organization.id
        ).join(
            ReportTemplate, ReportAssignment.report_template_id == ReportTemplate.id
        ).filter(
            ReportAssignment.status == ReportStatus.PENDING,
            ReportAssignment.due_date >= datetime.utcnow(),
            ReportAssignment.due_date <= datetime.utcnow() + timedelta(days=7)
        ).order_by(
            ReportAssignment.due_date
        ).limit(10).all()

    # Stats for unit users
    else:
        # Only show reports for this user's organization
        org_id = current_user.organization_id

        total_reports = ReportAssignment.query.filter_by(organization_id=org_id).count()
        pending_reports = ReportAssignment.query.filter_by(organization_id=org_id, status=ReportStatus.PENDING).count()
        submitted_reports = ReportAssignment.query.filter_by(organization_id=org_id, status=ReportStatus.SUBMITTED).count()
        overdue_reports = ReportAssignment.query.filter_by(organization_id=org_id, status=ReportStatus.OVERDUE).count()

        # Recent submissions from this organization only
        recent_submissions = db.session.query(
            ReportSubmission, User, Organization, ReportTemplate
        ).join(
            ReportAssignment, ReportSubmission.report_assignment_id == ReportAssignment.id
        ).join(
            User, ReportSubmission.submitted_by == User.id
        ).join(
            Organization, User.organization_id == Organization.id
        ).join(
            ReportTemplate, ReportAssignment.report_template_id == ReportTemplate.id
        ).filter(
            Organization.id == org_id
        ).order_by(
            ReportSubmission.submitted_at.desc()
        ).limit(10).all()

        # Upcoming deadlines for this organization only
        upcoming_deadlines = db.session.query(
            ReportAssignment, Organization, ReportTemplate
        ).join(
            Organization, ReportAssignment.organization_id == Organization.id
        ).join(
            ReportTemplate, ReportAssignment.report_template_id == ReportTemplate.id
        ).filter(
            Organization.id == org_id,
            ReportAssignment.status == ReportStatus.PENDING,
            ReportAssignment.due_date >= datetime.utcnow(),
            ReportAssignment.due_date <= datetime.utcnow() + timedelta(days=7)
        ).order_by(
            ReportAssignment.due_date
        ).limit(10).all()

    return render_template(
        'dashboard.html',
        total_reports=total_reports,
        pending_reports=pending_reports,
        submitted_reports=submitted_reports,
        overdue_reports=overdue_reports,
        recent_submissions=recent_submissions,
        upcoming_deadlines=upcoming_deadlines
    )

@app.route('/change_language', methods=['POST'])
def change_language():
    form = ChangeLanguageForm()
    if form.validate_on_submit():
        session['language'] = form.language.data
        if current_user.is_authenticated:
            current_user.language = form.language.data
            db.session.commit()
    return redirect(request.referrer or url_for('index'))

@app.route('/user_management')
@login_required
def user_management():
    # Only admin can access user management
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    users = db.session.query(
        User, Role, Organization
    ).join(
        Role, User.role_id == Role.id
    ).join(
        Organization, User.organization_id == Organization.id
    ).all()

    return render_template('user_management.html', users=users)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Only admin can edit users
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    form.role.choices = [(r.id, r.description) for r in Role.query.all()]
    form.organization.choices = [(o.id, o.name) for o in Organization.query.filter_by(is_active=True).all()]

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.fullname = form.fullname.data
        user.role_id = form.role.data
        user.organization_id = form.organization.data
        user.is_active = form.is_active.data

        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        log_action(current_user.id, 'edit_user', f'Edited user: {user.username}', request.remote_addr)
        flash('User updated successfully!', 'success')
        return redirect(url_for('user_management'))

    return render_template('register.html', form=form, edit=True)

@app.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
def toggle_user_status(user_id):
    # Only admin can toggle user status
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    # Cannot toggle status of the current user
    if user.id == current_user.id:
        flash('You cannot change your own account status.', 'danger')
        return redirect(url_for('user_management'))

    # Toggle the active status
    user.is_active = not user.is_active

    if user.is_active:
        action_type = 'activate_user'
        message = f'Activated user: {user.username}'
        flash_message = 'User activated successfully!'
    else:
        action_type = 'deactivate_user'
        message = f'Deactivated user: {user.username}'
        flash_message = 'User deactivated successfully!'

    db.session.commit()
    log_action(current_user.id, action_type, message, request.remote_addr)
    flash(flash_message, 'success')
    return redirect(url_for('user_management'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # For backwards compatibility, just call toggle_user_status
    user = User.query.get_or_404(user_id)
    if user.is_active:  # Only deactivate if currently active
        return toggle_user_status(user_id)
    else:
        # Already inactive
        flash('User is already deactivated.', 'info')
        return redirect(url_for('user_management'))

@app.route('/organization_management')
@login_required
def organization_management():
    # Only admin can access organization management
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    organizations = Organization.query.all()
    return render_template('organization_management.html', organizations=organizations)

@app.route('/add_organization', methods=['GET', 'POST'])
@login_required
def add_organization():
    # Only admin can add organizations
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    form = OrganizationForm()
    form.parent.choices = [(0, 'None')] + [(o.id, o.name) for o in Organization.query.all()]

    if form.validate_on_submit():
        organization = Organization(
            name=form.name.data,
            name_en=form.name_en.data,
            code=form.code.data,
            description=form.description.data,
            parent_id=form.parent.data if form.parent.data != 0 else None,
            is_active=form.is_active.data
        )
        db.session.add(organization)
        db.session.commit()
        log_action(current_user.id, 'add_organization', f'Added organization: {organization.name}', request.remote_addr)
        flash('Organization added successfully!', 'success')
        return redirect(url_for('organization_management'))

    return render_template('organization_management.html', form=form, add=True)

@app.route('/edit_organization/<int:org_id>', methods=['GET', 'POST'])
@login_required
def edit_organization(org_id):
    # Only admin can edit organizations
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    organization = Organization.query.get_or_404(org_id)
    form = OrganizationForm(obj=organization)
    form.parent.choices = [(0, 'None')] + [(o.id, o.name) for o in Organization.query.filter(Organization.id != org_id).all()]

    if request.method == 'GET':
        form.parent.data = organization.parent_id if organization.parent_id else 0
        form.id.data = org_id  # Set the ID field for validation

    if form.validate_on_submit():
        organization.name = form.name.data
        organization.name_en = form.name_en.data
        organization.code = form.code.data
        organization.description = form.description.data
        organization.parent_id = form.parent.data if form.parent.data != 0 else None
        organization.is_active = form.is_active.data
        db.session.commit()
        log_action(current_user.id, 'edit_organization', f'Edited organization: {organization.name}', request.remote_addr)
        flash('Organization updated successfully!', 'success')
        return redirect(url_for('organization_management'))

    return render_template('organization_management.html', form=form, edit=True, organization=organization)

@app.route('/report_templates')
@login_required
def report_templates():
    # Only admin and department users can access report templates
    if not current_user.is_admin() and not current_user.is_department():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    templates = ReportTemplate.query.all()
    return render_template('report_templates.html', templates=templates)

@app.route('/add_report_template', methods=['GET', 'POST'])
@login_required
def add_report_template():
    # Only admin and department users can add report templates
    if not current_user.is_admin() and not current_user.is_department():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    form = ReportTemplateForm()

    if form.validate_on_submit():
        app.logger.info(f"Form data: {form.data}")

        try:
            structure = json.loads(form.structure.data)
            if not structure or not isinstance(structure, dict) or 'sheets' not in structure:
                flash('Invalid template structure', 'danger')
                return render_template('report_template_form.html', form=form, add=True)

            if not structure['sheets']:
                flash('Template must have at least one sheet', 'danger')
                return render_template('report_template_form.html', form=form, add=True)

            # Validate sheet structure
            for sheet in structure['sheets']:
                if not sheet.get('fields'):
                    flash('Each sheet must have at least one field', 'danger')
                    return render_template('report_template_form.html', form=form, add=True)

            template = ReportTemplate(
                name=form.name.data,
                name_en=form.name_en.data,
                description=form.description.data,
                created_by=current_user.id,
                is_active=form.is_active.data,
                structure=json.dumps(structure) # Fix: Ensure structure is properly JSON encoded
            )

            db.session.add(template)
            db.session.commit()
            app.logger.info(f"Successfully created template: {template.name} (ID: {template.id})")
            flash('Report template created successfully!', 'success')
            return redirect(url_for('report_templates'))

        except Exception as e:
            app.logger.error(f"Error creating template: {str(e)}")
            db.session.rollback()
            flash(f'Error creating template: {str(e)}', 'danger')
            return render_template('report_template_form.html', form=form, add=True)
        # Log the form data for debugging
        app.logger.info(f"Form submitted with data: {form.data}")
        app.logger.info(f"Structure data: {form.structure.data}")

        # Validate JSON structure
        try:
            if isinstance(form.structure.data, str):
                app.logger.debug(f"Structure data: {form.structure.data}")
                structure = json.loads(form.structure.data)

                # Basic validation
                if not isinstance(structure, dict) or 'sheets' not in structure:
                    raise ValueError('Invalid template structure: Missing sheets')

                # Check that sheets is a list and has at least one element
                if not isinstance(structure['sheets'], list) or len(structure['sheets']) == 0:
                    raise ValueError('Invalid template structure: No sheets defined')

                # Check each sheet has a name and fields
                for i, sheet in enumerate(structure['sheets']):
                    if 'name' not in sheet or not sheet['name']:
                        raise ValueError(f'Sheet {i+1} has no name')

                    if 'fields' not in sheet or not isinstance(sheet['fields'], list) or len(sheet['fields']) == 0:
                        raise ValueError(f'Sheet {sheet["name"]} has no fields')

                    # Check each field has a name and type
                    for j, field in enumerate(sheet['fields']):
                        if 'name' not in field or not field['name']:
                            raise ValueError(f'Field {j+1} in sheet {sheet["name"]} has no name')

                        if 'type' not in field:
                            raise ValueError(f'Field {field["name"]} in sheet {sheet["name"]} has no type')
            else:
                flash('Invalid template structure: Not a valid JSON string', 'danger')
                return render_template('report_template_form.html', form=form, add=True)
        except json.JSONDecodeError as e:
            app.logger.error(f"JSON decode error: {str(e)}")
            flash(f'Invalid template structure: Not valid JSON - {str(e)}', 'danger')
            return render_template('report_template_form.html', form=form, add=True)
        except Exception as e:
            app.logger.error(f"Structure validation error: {str(e)}")
            flash(f'Invalid template structure: {str(e)}', 'danger')
            return render_template('report_template_form.html', form=form, add=True)

        try:
            template = ReportTemplate(
                name=form.name.data,
                name_en=form.name_en.data,
                description=form.description.data,
                created_by=current_user.id,
                is_active=form.is_active.data,
                structure=form.structure.data
            )
            db.session.add(template)
            db.session.commit()
            log_action(current_user.id, 'add_report_template', f'Added report template: {template.name}', request.remote_addr)
            app.logger.info(f"Successfully added template: {template.name} (ID: {template.id})")
            flash('Report template added successfully!', 'success')
            return redirect(url_for('report_templates'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error saving template: {str(e)}")
            flash(f'Error saving report template: {str(e)}', 'danger')
            return render_template('report_template_form.html', form=form, add=True)

    return render_template('report_template_form.html', form=form, add=True)

@app.route('/edit_report_template/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_report_template(template_id):
    # Only admin and department users can edit report templates
    if not current_user.is_admin() and not current_user.is_department():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    template = ReportTemplate.query.get_or_404(template_id)
    form = ReportTemplateForm(obj=template)

    if request.method == 'GET':
        form.structure.data = template.structure

    if form.validate_on_submit():
        # Log the form data for debugging
        app.logger.info(f"Form submitted with data: {form.data}")
        app.logger.info(f"Structure data: {form.structure.data}")

        # Validate JSON structure
        try:
            if isinstance(form.structure.data, str):
                app.logger.debug(f"Structure data: {form.structure.data}")
                structure = json.loads(form.structure.data)

                # Basic validation
                if not isinstance(structure, dict) or 'sheets' not in structure:
                    raise ValueError('Invalid template structure: Missing sheets')

                # Check that sheets is a list and has at least one element
                if not isinstance(structure['sheets'], list) or len(structure['sheets']) == 0:
                    raise ValueError('Invalid template structure: No sheets defined')

                # Check each sheet has a name and fields
                for i, sheet in enumerate(structure['sheets']):
                    if 'name' not in sheet or not sheet['name']:
                        raise ValueError(f'Sheet {i+1} has no name')

                    if 'fields' not in sheet or not isinstance(sheet['fields'], list) or len(sheet['fields']) == 0:
                        raise ValueError(f'Sheet {sheet["name"]} has no fields')

                    # Check each field has a name and type
                    for j, field in enumerate(sheet['fields']):
                        if 'name' not in field or not field['name']:
                            raise ValueError(f'Field {j+1} in sheet {sheet["name"]} has no name')

                        if 'type' not in field:
                            raise ValueError(f'Field {field["name"]} in sheet {sheet["name"]} has no type')
            else:
                flash('Invalid template structure: Not a valid JSON string', 'danger')
                return render_template('report_template_form.html', form=form, edit=True, template=template)
        except json.JSONDecodeError as e:
            app.logger.error(f"JSON decode error: {str(e)}")
            flash(f'Invalid template structure: Not valid JSON - {str(e)}', 'danger')
            return render_template('report_template_form.html', form=form, edit=True, template=template)
        except Exception as e:
            app.logger.error(f"Structure validation error: {str(e)}")
            flash(f'Invalid template structure: {str(e)}', 'danger')
            return render_template('report_template_form.html', form=form, edit=True, template=template)

        try:
            template.name = form.name.data
            template.name_en = form.name_en.data
            template.description = form.description.data
            template.is_active = form.is_active.data
            template.structure = form.structure.data
            template.updated_at = datetime.utcnow()
            db.session.commit()
            log_action(current_user.id, 'edit_report_template', f'Edited report template: {template.name}', request.remote_addr)
            app.logger.info(f"Successfully updated template: {template.name} (ID: {template.id})")
            flash('Report template updated successfully!', 'success')
            return redirect(url_for('report_templates'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating template: {str(e)}")
            flash(f'Error updating report template: {str(e)}', 'danger')
            return render_template('report_template_form.html', form=form, edit=True, template=template)

    return render_template('report_template_form.html', form=form, edit=True, template=template)

@app.route('/delete_report_template/<int:template_id>', methods=['POST'])
@login_required
def delete_report_template(template_id):
    # Only admin and department users can delete report templates
    if not current_user.is_admin() and not current_user.is_department():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    template = ReportTemplate.query.get_or_404(template_id)

    # Check if the template has any assignments
    if ReportAssignment.query.filter_by(report_template_id=template_id).first():
        flash('Cannot delete a template that has assignments. Deactivate it instead.', 'danger')
        return redirect(url_for('report_templates'))

    db.session.delete(template)
    db.session.commit()
    log_action(current_user.id, 'delete_report_template', f'Deleted report template: {template.name}', request.remote_addr)
    flash('Report template deleted successfully!', 'success')
    return redirect(url_for('report_templates'))

@app.route('/report_assignments')
@login_required
def report_assignments():
    # Filter assignments based on user role
    if current_user.is_admin():
        assignments = db.session.query(
            ReportAssignment, Organization, ReportTemplate
        ).join(
            Organization, ReportAssignment.organization_id == Organization.id
        ).join(
            ReportTemplate, ReportAssignment.report_template_id == ReportTemplate.id
        ).all()
    elif current_user.is_department():
        # Department users can see all assignments but might want to filter by their department
        assignments = db.session.query(
            ReportAssignment, Organization, ReportTemplate
        ).join(
            Organization, ReportAssignment.organization_id == Organization.id
        ).join(
            ReportTemplate, ReportAssignment.report_template_id == ReportTemplate.id
        ).all()
    else:
        # Unit users can only see their own assignments
        assignments = db.session.query(
            ReportAssignment, Organization, ReportTemplate
        ).join(
            Organization, ReportAssignment.organization_id == Organization.id
        ).join(
            ReportTemplate, ReportAssignment.report_template_id == ReportTemplate.id
        ).filter(
            ReportAssignment.organization_id == current_user.organization_id
        ).all()

    return render_template('report_assignments.html', assignments=assignments)

@app.route('/add_report_assignment', methods=['GET', 'POST'])
@login_required
def add_report_assignment():
    # Only admin and department users can add report assignments
    if not current_user.is_admin() and not current_user.is_department():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    form = ReportAssignmentForm()

    # Load active templates
    templates = ReportTemplate.query.filter_by(is_active=True).all()
    form.report_templates.choices = [(t.id, f"{t.name} ({t.name_en})" if t.name_en else t.name) for t in templates]

    # Load active organizations
    if current_user.is_admin():
        orgs = Organization.query.filter_by(is_active=True).all()
    else:
        # For department users, only show related organizations
        orgs = Organization.query.filter_by(is_active=True, parent_id=current_user.organization_id).all()

    form.organizations.choices = [(o.id, f"{o.name} ({o.code})") for o in orgs]

    # Department users can only assign to their department's organizations
    if current_user.is_admin():
        form.organizations.choices = [(o.id, o.name) for o in Organization.query.filter_by(is_active=True).all()]
    else:
        # For department users, we'd need to filter organizations by department
        # This would require a relationship between departments and organizations
        # For now, let's assume department users can assign to all organizations
        form.organizations.choices = [(o.id, o.name) for o in Organization.query.filter_by(is_active=True).all()]

    if form.validate_on_submit():
        # Create multiple assignments based on the cross-product of templates and organizations
        assignments_count = 0
        for template_id in form.report_templates.data:
            for org_id in form.organizations.data:
                assignment = ReportAssignment(
                    report_template_id=template_id,
                    organization_id=org_id,
                    due_date=form.due_date.data,
                    frequency=ReportFrequency(form.frequency.data),
                    status=ReportStatus.PENDING
                )
                db.session.add(assignment)
                assignments_count += 1

        db.session.commit()
        log_action(
            current_user.id, 
            'add_report_assignment', 
            f'Added {assignments_count} report assignments', 
            request.remote_addr
        )
        flash(f'{assignments_count} report assignments added successfully!', 'success')
        return redirect(url_for('report_assignments'))

    return render_template('report_assignments.html', form=form, add=True)

@app.route('/view_report_submission/<int:assignment_id>')
@login_required
def view_report_submission(assignment_id):
    assignment = ReportAssignment.query.get_or_404(assignment_id)

    # Check if the user has permission to view this assignment
    if not current_user.is_admin() and not current_user.is_department():
        if assignment.organization_id != current_user.organization_id:
            flash('You do not have permission to view this report.', 'danger')
            return redirect(url_for('report_assignments'))

    template = ReportTemplate.query.get(assignment.report_template_id)
    organization = Organization.query.get(assignment.organization_id)
    submissions = ReportSubmission.query.filter_by(report_assignment_id=assignment_id).order_by(ReportSubmission.submitted_at.desc()).all()

    # Get the structure of the template
    template_structure = json.loads(template.structure)

    return render_template(
        'report_submission.html',
        assignment=assignment,
        template=template,
        organization=organization,
        submissions=submissions,
        template_structure=template_structure,
        view_only=True
    )

@app.route('/submit_report/<int:assignment_id>', methods=['GET', 'POST'])
@login_required
def submit_report(assignment_id):
    assignment = ReportAssignment.query.get_or_404(assignment_id)

    # Only users from the assigned organization can submit reports
    if assignment.organization_id != current_user.organization_id and not current_user.is_admin():
        flash('You do not have permission to submit this report.', 'danger')
        return redirect(url_for('report_assignments'))

    template = ReportTemplate.query.get(assignment.report_template_id)
    organization = Organization.query.get(assignment.organization_id)

    form = ReportSubmissionForm()

    if form.validate_on_submit():
        try:
            # Process the submission
            submitted_data = None
            sharepoint_path = None
            filename = None
            app.logger.info("Processing form submission...")app.logger.debug(f"Form data: {form.form_data.data}")

            # Check if there's form data or a file
            if form.form_data.data:
                app.logger.info("Processing form data submission")
                # Process form data
                submitted_data = form.form_data.data
                if not submitted_data:
                    flash('Please fill in the required data.', 'danger')
                    return render_template(
                        'report_submission.html',
                        form=form,
                        assignment=assignment,
                        template=template,
                        organization=organization,
                        template_structure=json.loads(template.structure)
                    )

                # Get settings
                sharepoint_setting = Settings.query.filter_by(key='sharepoint_url').first()
                sharepoint_url = sharepoint_setting.value if sharepoint_setting else DEFAULT_SETTINGS['sharepoint_url']

                # Create directory structure
                today = datetime.now().strftime('%Y-%m-%d')
                org_code = organization.code
                template_name = template.name.replace(' ', '_')
                directory = f"reports/{today}/{org_code}/{template_name}"
                os.makedirs(directory, exist_ok=True)

                # Generate filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{org_code}_{template_name}_{timestamp}.xlsx"
                filepath = os.path.join(directory, filename)

                # Generate Excel
                generate_excel(json.loads(submitted_data), template.get_structure(), filepath)

                # Set Sharepoint path
                sharepoint_path = f"{sharepoint_url}/{filepath}"

            elif 'file' in request.files and request.files['file'].filename:
                # Process file upload
                file = request.files['file']
                try:
                    # Get settings
                    sharepoint_setting = Settings.query.filter_by(key='sharepoint_url').first()
                    sharepoint_url = sharepoint_setting.value if sharepoint_setting else DEFAULT_SETTINGS['sharepoint_url']

                    # Create directory structure
                    today = datetime.now().strftime('%Y-%m-%d')
                    org_code = organization.code
                    template_name = template.name.replace(' ', '_')
                    directory = f"reports/{today}/{org_code}/{template_name}"
                    os.makedirs(directory, exist_ok=True)

                    # Generate filename
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    original_filename = file.filename
                    extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'xlsx'
                    filename = f"{org_code}_{template_name}_{timestamp}.{extension}"
                    filepath = os.path.join(directory, filename)

                    # Save file
                    file.save(filepath)

                    # Set Sharepoint path
                    sharepoint_path = f"{sharepoint_url}/{filepath}"

                except Exception as e:
                    flash(f'Error uploading file: {str(e)}', 'danger')
                    return render_template(
                        'report_submission.html',
                        form=form,
                        assignment=assignment,
                        template=template,
                        organization=organization
                    )

            else:
                flash('Please submit either form data or a file.', 'danger')
                return render_template(
                    'report_submission.html',
                    form=form,
                    assignment=assignment,
                    template=template,
                    organization=organization
                )

            # Create submission record
            submission = ReportSubmission(
                report_assignment_id=assignment_id,
                submitted_by=current_user.id,
                sharepoint_path=sharepoint_path,
                filename=filename,
                notes=form.notes.data,
                form_data=submitted_data
            )
            db.session.add(submission)

            # Update assignment status
            assignment.status = ReportStatus.SUBMITTED

            try:
                db.session.commit()
                log_action(current_user.id, 'submit_report', f'Submitted report for assignment ID: {assignment.id}', request.remote_addr)
                app.logger.info(f"Report submitted successfully for assignment {assignment.id}")
                flash('Report submitted successfully!', 'success')
                return redirect(url_for('report_assignments'))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error submitting report: {str(e)}")
                flash(f'Error submitting report: {str(e)}', 'danger')
                return render_template(
                    'report_submission.html',
                    form=form,
                    assignment=assignment,
                    template=template,
                    organization=organization,
                    template_structure=json.loads(template.structure)
                )

            # Send notification email (if enabled)
            email_setting = Settings.query.filter_by(key='email_notifications').first()
            if email_setting and email_setting.value == 'True':
                # Find department users to notify
                if current_user.role.name == 'unit':
                    department_users = User.query.join(Role).filter(Role.name == 'department').all()
                    for user in department_users:
                        subject = f"New report submission: {template.name}"
                        body = f"""
                        A new report has been submitted:

                        Organization: {organization.name}
                        Report: {template.name}
                        Submitted by: {current_user.fullname}
                        Submission time: {submission.submitted_at}

                        Please log in to review the report.
                        """
                        send_email(user.email, subject, body)

            flash('Report submitted successfully!', 'success')
            return redirect(url_for('report_assignments'))

        except Exception as e:
            db.session.rollback()
            app.logger.exception(f"An unexpected error occurred: {e}")
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
            return render_template(
                'report_submission.html',
                form=form,
                assignment=assignment,
                template=template,
                organization=organization,
                template_structure=json.loads(template.structure)
            )

    # Get the structure of the template for rendering the form
    template_structure = json.loads(template.structure)

    return render_template(
        'report_submission.html',
        form=form,
        assignment=assignment,
        template=template,
        organization=organization,
        template_structure=template_structure
    )

@app.route('/download_report/<int:submission_id>')
@login_required
def download_report(submission_id):
    submission = ReportSubmission.query.get_or_404(submission_id)
    assignment = ReportAssignment.query.get(submission.report_assignment_id)

    # Check if the user has permission to download this report
    if not current_user.is_admin() and not current_user.is_department():
        if assignment.organization_id != current_user.organization_id:
            flash('You do not have permission to download this report.', 'danger')
            return redirect(url_for('report_assignments'))

    # Check if the report exists
    if not submission.sharepoint_path or not submission.filename:
        flash('The report file is not available.', 'danger')
        return redirect(url_for('view_report_submission', assignment_id=assignment.id))

    # Extract the local file path from the Sharepoint path
    sharepoint_setting = Settings.query.filter_by(key='sharepoint_url').first()
    sharepoint_url = sharepoint_setting.value if sharepoint_setting else DEFAULT_SETTINGS['sharepoint_url']

    if submission.sharepoint_path.startswith(sharepoint_url):
        local_path = submission.sharepoint_path[len(sharepoint_url):]
    else:
        local_path = submission.sharepoint_path

    # If the path starts with a slash, remove it
    if local_path.startswith('/'):
        local_path = local_path[1:]

    if not os.path.exists(local_path):
        flash('The report file could not be found.', 'danger')
        return redirect(url_for('view_report_submission', assignment_id=assignment.id))

    return send_file(local_path, as_attachment=True, download_name=submission.filename)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    # Only admin can access settings
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    form = SettingsForm()

    # Load current settings
    if request.method == 'GET':
        for key in DEFAULT_SETTINGS:
            setting = Settings.query.filter_by(key=key).first()
            if setting:
                if hasattr(form, key):
                    # Special handling for boolean fields
                    if key == 'email_notifications':
                        setattr(form, key, setting.value == 'True')
                    else:
                        setattr(form, key, setting.value)

    if form.validate_on_submit():
        # Update settings
        for key in DEFAULT_SETTINGS:
            if hasattr(form, key):
                value = getattr(form, key)
                # Special handling for boolean fields
                if key == 'email_notifications':
                    value = str(value)

                setting = Settings.query.filter_by(key=key).first()
                if setting:
                    setting.value = value
                else:
                    setting = Settings(key=key, value=value, description=key)
                    db.session.add(setting)

        db.session.commit()
        log_action(current_user.id, 'update_settings', 'Updated system settings', request.remote_addr)
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', form=form)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('change_password.html', form=form)

        current_user.set_password(form.new_password.data)
        db.session.commit()
        log_action(current_user.id, 'change_password', 'Changed password', request.remote_addr)
        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('change_password.html', form=form)

@app.route('/reports_overview')
@login_required
def reports_overview():
    # Only admin and department users can access reports overview
    if not current_user.is_admin() and not current_user.is_department():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    # Get statistics for charts
    organizations = Organization.query.filter_by(is_active=True).all()
    org_names = [org.name for org in organizations]

    submission_stats = []
    for org in organizations:
        total = ReportAssignment.query.filter_by(organization_id=org.id).count()
        submitted = ReportAssignment.query.filter_by(organization_id=org.id, status=ReportStatus.SUBMITTED).count()
        pending = ReportAssignment.query.filter_by(organization_id=org.id, status=ReportStatus.PENDING).count()
        overdue = ReportAssignment.query.filter_by(organization_id=org.id, status=ReportStatus.OVERDUE).count()

        submission_stats.append({
            'organization': org.name,
            'total': total,
            'submitted': submitted,
            'pending': pending,
            'overdue': overdue,
            'completion_rate': (submitted / total * 100) if total > 0 else 0
        })

    # Get monthly submission counts for the past year
    monthly_data = []
    today = datetime.utcnow()
    for i in range(12):
        month_start = datetime(today.year, today.month, 1) - timedelta(days=30*i)
        month_end = datetime(month_start.year, month_start.month + 1, 1) if month_start.month < 12 else datetime(month_start.year + 1, 1, 1)
        month_name = month_start.strftime('%b %Y')

        count = ReportSubmission.query.filter(
            ReportSubmission.submitted_at >= month_start,
            ReportSubmission.submitted_at < month_end
        ).count()

        monthly_data.append({
            'month': month_name,
            'count': count
        })

    # Reverse the list to show oldest to newest
    monthly_data.reverse()

    return render_template(
        'reports_overview.html',
        org_names=org_names,
        submission_stats=submission_stats,
        monthly_data=monthly_data
    )

@app.route('/api/report_template/<int:template_id>')
@login_required
def api_report_template(template_id):
    template = ReportTemplate.query.get_or_404(template_id)
    return jsonify({
        'id': template.id,
        'name': template.name,
        'name_en': template.name_en,
        'description': template.description,
        'structure': template.get_structure()
    })

@app.route('/initialize_sample_data')
@login_required
def initialize_sample_data():
    # Only admin can initialize sample data
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    # Check if there are already templates
    if ReportTemplate.query.first():
        flash('Sample data already exists. To reset, please use the database management tools.', 'info')
        return redirect(url_for('dashboard'))

    # Add sample report templates
    for template_data in SAMPLE_REPORT_TEMPLATES:
        try:
            template = ReportTemplate(
                name=template_data['name'],
                name_en=template_data['name_en'],
                description=template_data['description'],
                created_by=current_user.id,
                is_active=True,
                structure=json.dumps(template_data['structure'])
            )
            db.session.add(template)
            db.session.flush()  # Flush to get the template ID without committing
            app.logger.info(f"Added template: {template.name}, ID: {template.id}")
        except Exception as e:
            app.logger.error(f"Error adding template {template_data['name']}: {str(e)}")
            flash(f"Error adding template {template_data['name']}: {str(e)}", 'danger')
            db.session.rollback()
            return redirect(url_for('dashboard'))

    # Add default settings if they don't exist
    for key, value in DEFAULT_SETTINGS.items():
        if not Settings.query.filter_by(key=key).first():
            setting = Settings(
                key=key,
                value=value,
                description=key
            )
            db.session.add(setting)

    try:
        db.session.commit()
        log_action(current_user.id, 'initialize_sample_data', 'Initialized sample data', request.remote_addr)
        flash('Sample data initialized successfully!', 'success')
    except Exception as e:
        app.logger.error(f"Error committing sample data: {str(e)}")
        flash(f"Error saving sample data: {str(e)}", 'danger')
        db.session.rollback()

    return redirect(url_for('dashboard'))

@app.route('/initialize_sample_assignments')
@login_required
def initialize_sample_assignments():
    # Only admin can initialize sample assignments
    if not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('dashboard'))

    # Check if there are already assignments
    if ReportAssignment.query.first():
        flash('Sample assignments already exist. To reset, please use the database management tools.', 'info')
        return redirect(url_for('dashboard'))

    # Get templates
    templates = ReportTemplate.query.filter_by(is_active=True).all()
    if not templates:
        flash('No report templates found. Please initialize sample data first.', 'warning')
        return redirect(url_for('dashboard'))

    # Get organizations (excluding root Vinatex)
    orgs = Organization.query.filter(Organization.parent_id.isnot(None)).filter_by(is_active=True).all()
    if not orgs:
        flash('No member organizations found. Please add member organizations first.', 'warning')
        return redirect(url_for('dashboard'))

    # Create assignments
    assignments_count = 0
    today = datetime.now()
    next_month = today + timedelta(days=30)

    try:
        # Financial reports for all orgs
        financial_template = ReportTemplate.query.filter(ReportTemplate.name.like('%tài chính%')).first()
        if financial_template:
            for org in orgs:
                assignment = ReportAssignment(
                    report_template_id=financial_template.id,
                    organization_id=org.id,
                    due_date=next_month,
                    frequency=ReportFrequency.MONTHLY,
                    status=ReportStatus.PENDING
                )
                db.session.add(assignment)
                assignments_count += 1

        # Production reports for all orgs
        production_template = ReportTemplate.query.filter(ReportTemplate.name.like('%sản xuất%')).first()
        if production_template:
            for org in orgs:
                assignment = ReportAssignment(
                    report_template_id=production_template.id,
                    organization_id=org.id,
                    due_date=next_month,
                    frequency=ReportFrequency.MONTHLY,
                    status=ReportStatus.PENDING
                )
                db.session.add(assignment)
                assignments_count += 1

        # Investment plan for specific orgs (first 3)
        investment_template = ReportTemplate.query.filter(ReportTemplate.name.like('%kế hoạch đầu tư%')).first()
        if investment_template and len(orgs) >= 3:
            for org in orgs[:3]:
                assignment = ReportAssignment(
                    report_template_id=investment_template.id,
                    organization_id=org.id,
                    due_date=next_month + timedelta(days=30),  # Due in 2 months
                    frequency=ReportFrequency.QUARTERLY,
                    status=ReportStatus.PENDING
                )
                db.session.add(assignment)
                assignments_count += 1

        # Create a past-due assignment for demonstration
        if financial_template and orgs:
            last_month = today - timedelta(days=15)
            assignment = ReportAssignment(
                report_template_id=financial_template.id,
                organization_id=orgs[0].id,
                due_date=last_month,
                frequency=ReportFrequency.MONTHLY,
                status=ReportStatus.OVERDUE
            )
            db.session.add(assignment)
            assignments_count += 1

        db.session.commit()
        log_action(current_user.id, 'initialize_sample_assignments', f'Initialized {assignments_count} sample assignments', request.remote_addr)
        flash(f'Successfully created {assignments_count} sample report assignments!', 'success')

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating sample assignments: {str(e)}")
        flash(f'Error creating sample assignments: {str(e)}', 'danger')

    return redirect(url_for('report_assignments'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="404 - Page Not Found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error="500 - Internal Server Error"), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error="403 - Forbidden"), 403

@app.errorhandler(400)
def bad_request(e):
    return render_template('error.html', error="400 - Bad Request"), 400