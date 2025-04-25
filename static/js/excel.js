// Vinatex Report Portal - Excel Handling

// Function to convert form data to Excel format
function convertFormDataToExcel(formData, structure) {
    // Create a new workbook
    const workbook = XLSX.utils.book_new();
    
    // Process each sheet
    structure.sheets.forEach(sheet => {
        // Create an array of rows for this sheet
        const rows = [];
        
        // Add header row with labels
        const headers = sheet.fields.map(field => field.label);
        rows.push(headers);
        
        // Add data row with values from form data
        const dataRow = [];
        sheet.fields.forEach(field => {
            const fieldName = field.name;
            const value = formData[fieldName] || '';
            dataRow.push(value);
        });
        rows.push(dataRow);
        
        // Create worksheet from the rows
        const ws = XLSX.utils.aoa_to_sheet(rows);
        
        // Add the worksheet to the workbook
        XLSX.utils.book_append_sheet(workbook, ws, sheet.name);
    });
    
    // Generate Excel file
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    
    return excelBuffer;
}

// Function to download Excel file
function downloadExcel(excelBuffer, filename) {
    // Convert buffer to Blob
    const blob = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
    
    // Create download link
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || 'report.xlsx';
    document.body.appendChild(link);
    link.click();
    
    // Clean up
    setTimeout(() => {
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }, 0);
}

// Function to read Excel file and extract data
function readExcelFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            try {
                const data = new Uint8Array(e.target.result);
                const workbook = XLSX.read(data, { type: 'array' });
                
                // Process each sheet
                const result = {};
                workbook.SheetNames.forEach(sheetName => {
                    const worksheet = workbook.Sheets[sheetName];
                    const sheetData = XLSX.utils.sheet_to_json(worksheet);
                    result[sheetName] = sheetData;
                });
                
                resolve(result);
            } catch (error) {
                reject(error);
            }
        };
        
        reader.onerror = function(error) {
            reject(error);
        };
        
        reader.readAsArrayBuffer(file);
    });
}

// Function to validate Excel data against template structure
function validateExcelData(excelData, structure) {
    const errors = [];
    
    // Check if all required sheets exist
    structure.sheets.forEach(sheet => {
        const sheetName = sheet.name;
        if (!excelData[sheetName]) {
            errors.push(`Missing sheet: ${sheetName}`);
            return;
        }
        
        // Check if each sheet has data
        if (!excelData[sheetName].length) {
            errors.push(`Empty sheet: ${sheetName}`);
            return;
        }
        
        // Check if required fields exist in the first row
        const firstRow = excelData[sheetName][0];
        sheet.fields.forEach(field => {
            if (field.required && !(field.label in firstRow)) {
                errors.push(`Missing required field "${field.label}" in sheet "${sheetName}"`);
            }
        });
    });
    
    return {
        valid: errors.length === 0,
        errors: errors
    };
}

// Function to generate a template Excel file from structure
function generateTemplateExcel(structure) {
    // Create a new workbook
    const workbook = XLSX.utils.book_new();
    
    // Process each sheet
    structure.sheets.forEach(sheet => {
        // Create an array of rows for this sheet
        const rows = [];
        
        // Add header row with labels
        const headers = sheet.fields.map(field => field.label);
        rows.push(headers);
        
        // Add an empty row as an example
        const emptyRow = Array(headers.length).fill('');
        rows.push(emptyRow);
        
        // Create worksheet from the rows
        const ws = XLSX.utils.aoa_to_sheet(rows);
        
        // Add the worksheet to the workbook
        XLSX.utils.book_append_sheet(workbook, ws, sheet.name);
    });
    
    // Generate Excel file
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    
    return excelBuffer;
}

// Function to extract form data from Excel file
function extractFormDataFromExcel(excelData, structure) {
    const formData = {};
    
    structure.sheets.forEach(sheet => {
        const sheetName = sheet.name;
        if (excelData[sheetName] && excelData[sheetName].length > 0) {
            const rowData = excelData[sheetName][0]; // Get first row
            
            sheet.fields.forEach(field => {
                const fieldName = field.name;
                const fieldLabel = field.label;
                
                if (rowData.hasOwnProperty(fieldLabel)) {
                    formData[fieldName] = rowData[fieldLabel];
                }
            });
        }
    });
    
    return formData;
}
