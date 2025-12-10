# html_templates.py - All HTML Templates for JP Global InsectDetect

# Shared CSS and Sidebar Styles
SIDEBAR_STYLES = """
<style>
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
        min-height: 100vh;
        color: #ffffff;
        display: flex;
        overflow-x: hidden;
    }
    
    /* Mobile Menu Button (Hamburger) */
    .mobile-menu-btn {
        display: none;
        position: fixed;
        top: 20px;
        left: 20px;
        z-index: 2001;
        font-size: 28px;
        color: #ffffff;
        cursor: pointer;
        background: rgba(255, 127, 80, 0.15);
        width: 48px;
        height: 48px;
        border-radius: 12px;
        border: 1px solid rgba(255, 127, 80, 0.3);
        backdrop-filter: blur(10px);
        display: none;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
    }
    
    .mobile-menu-btn:hover {
        background: rgba(255, 127, 80, 0.25);
        transform: scale(1.05);
    }
    
    .mobile-menu-btn:active {
        transform: scale(0.95);
    }
    
    /* Overlay for mobile sidebar */
    .sidebar-overlay {
        display: none;
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        backdrop-filter: blur(4px);
        z-index: 999;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .sidebar-overlay.active {
        opacity: 1;
    }
    
    /* Sidebar Styles */
    .sidebar {
        width: 260px;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        padding: 24px 0;
        position: fixed;
        height: 100vh;
        left: 0;
        top: 0;
        overflow-y: auto;
        overflow-x: hidden;
        z-index: 1000;
        transition: transform 0.3s ease-in-out;
    }
    
    /* Sidebar scrollbar styling */
    .sidebar::-webkit-scrollbar {
        width: 6px;
    }
    
    .sidebar::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.02);
    }
    
    .sidebar::-webkit-scrollbar-thumb {
        background: rgba(255, 127, 80, 0.3);
        border-radius: 3px;
    }
    
    .sidebar::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 127, 80, 0.5);
    }
    
    .sidebar-logo {
        padding: 0 20px 24px 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        text-align: center;
    }
    
    .sidebar-logo img {
        width: 160px;
        height: auto;
        margin-bottom: 8px;
    }
    
    .sidebar-title {
        font-size: 14px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.5);
    }
    
    .sidebar-menu {
        padding: 20px 0;
    }
    
    .menu-item {
        display: flex;
        align-items: center;
        padding: 14px 24px;
        color: rgba(255, 255, 255, 0.7);
        text-decoration: none;
        transition: all 0.3s ease;
        font-size: 14px;
        font-weight: 500;
        border-left: 3px solid transparent;
    }
    
    .menu-item i {
        margin-right: 12px;
        font-size: 16px;
        width: 20px;
        text-align: center;
    }
    
    .menu-item:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #ff7f50;
        border-left-color: #ff7f50;
    }
    
    .menu-item.active {
        background: rgba(255, 127, 80, 0.1);
        color: #ff7f50;
        border-left-color: #ff7f50;
    }
    
    .menu-item.logout {
        color: #ff6b6b;
        margin-top: 20px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        padding-top: 24px;
    }
    
    .menu-item.logout:hover {
        background: rgba(255, 107, 107, 0.1);
        color: #ff6b6b;
        border-left-color: #ff6b6b;
    }
    
    /* Main Content Area */
    .main-content {
        margin-left: 260px;
        flex: 1;
        padding: 32px;
        width: calc(100% - 260px);
        min-height: 100vh;
        transition: margin-left 0.3s ease-in-out, width 0.3s ease-in-out;
    }
    
    .page-header {
        margin-bottom: 32px;
        padding-bottom: 20px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .page-title {
        font-size: 32px;
        font-weight: 700;
        background: linear-gradient(135deg, #ff7f50 0%, #409cff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }
    
    .page-subtitle {
        font-size: 14px;
        color: rgba(255, 255, 255, 0.5);
    }
    
    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 32px;
    }
    
    .stat-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-4px);
        border-color: rgba(255, 127, 80, 0.3);
        box-shadow: 0 8px 24px rgba(255, 127, 80, 0.15);
    }
    
    .stat-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 16px;
    }
    
    .stat-icon.orange {
        background: linear-gradient(135deg, rgba(255, 127, 80, 0.2) 0%, rgba(255, 127, 80, 0.05) 100%);
        color: #ff7f50;
    }
    
    .stat-icon.blue {
        background: linear-gradient(135deg, rgba(64, 156, 255, 0.2) 0%, rgba(64, 156, 255, 0.05) 100%);
        color: #409cff;
    }
    
    .stat-icon.green {
        background: linear-gradient(135deg, rgba(76, 217, 100, 0.2) 0%, rgba(76, 217, 100, 0.05) 100%);
        color: #4cd964;
    }
    
    .stat-icon.purple {
        background: linear-gradient(135deg, rgba(175, 82, 222, 0.2) 0%, rgba(175, 82, 222, 0.05) 100%);
        color: #af52de;
    }
    
    .stat-label {
        font-size: 13px;
        color: rgba(255, 255, 255, 0.6);
        margin-bottom: 4px;
    }
    
    .stat-value {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Chart Container */
    .chart-container {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
    }
    
    .chart-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        flex-wrap: wrap;
        gap: 16px;
    }
    
    .chart-title {
        font-size: 18px;
        font-weight: 600;
        color: #ffffff;
    }
    
    /* Table Styles */
    .table-container {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px;
        overflow-x: auto;
    }
    
    table {
        width: 100%;
        border-collapse: collapse;
        min-width: 600px;
    }
    
    thead tr {
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    th {
        padding: 12px 16px;
        text-align: left;
        font-size: 13px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.7);
        text-transform: uppercase;
    }
    
    td {
        padding: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.9);
        font-size: 14px;
    }
    
    tbody tr {
        transition: all 0.2s ease;
    }
    
    tbody tr:hover {
        background: rgba(255, 255, 255, 0.03);
    }
    
    /* Image Styles */
    .image-thumb {
        width: 120px;
        height: 80px;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .image-thumb:hover {
        transform: scale(1.05);
        border-color: #ff7f50;
    }
    
    .image-gallery {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 20px;
    }
    
    .image-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        overflow: hidden;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .image-card:hover {
        transform: translateY(-4px);
        border-color: rgba(255, 127, 80, 0.3);
    }
    
    .image-card img {
        width: 100%;
        height: 200px;
        object-fit: cover;
    }
    
    .image-card-info {
        padding: 12px;
    }
    
    .image-card-title {
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 4px;
    }
    
    .image-card-meta {
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
    }
    
    /* Form Styles */
    .form-container {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px;
        margin-bottom: 24px;
    }
    
    .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 20px;
        margin-bottom: 20px;
    }
    
    .form-group {
        margin-bottom: 20px;
    }
    
    .form-group label {
        display: block;
        color: rgba(255, 255, 255, 0.8);
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 8px;
    }
    
    .form-group input,
    .form-group select {
        width: 100%;
        padding: 12px 16px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: #ffffff;
        font-size: 14px;
        font-family: 'Poppins', sans-serif;
    }
    
    .form-group input:focus,
    .form-group select:focus {
        outline: none;
        background: rgba(255, 255, 255, 0.08);
        border-color: #ff7f50;
        box-shadow: 0 0 0 3px rgba(255, 127, 80, 0.1);
    }
    
    /* Buttons */
    .btn {
        padding: 12px 28px;
        border: none;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        font-family: 'Poppins', sans-serif;
        text-decoration: none;
        display: inline-block;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #ff7f50 0%, #ff6b45 100%);
        color: #ffffff;
    }
    
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(255, 127, 80, 0.3);
    }
    
    .btn-secondary {
        background: rgba(64, 156, 255, 0.15);
        color: #409cff;
        border: 1px solid rgba(64, 156, 255, 0.3);
    }
    
    .btn-secondary:hover {
        background: rgba(64, 156, 255, 0.25);
    }
    
    /* Filter Bar */
    .filter-bar {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        gap: 16px;
        flex-wrap: wrap;
    }
    
    .filter-bar select {
        flex: 1;
        min-width: 200px;
        padding: 10px 16px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: #ffffff;
        font-size: 14px;
    }
    
    /* Modal */
    .modal {
        display: none;
        position: fixed;
        z-index: 2000;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.9);
        backdrop-filter: blur(10px);
    }
    
    .modal-content {
        position: relative;
        margin: 5% auto;
        max-width: 800px;
        animation: zoomIn 0.3s ease;
        padding: 0 20px;
    }
    
    .modal-content img {
        width: 100%;
        border-radius: 12px;
    }
    
    .close-modal {
        position: absolute;
        top: -40px;
        right: 0;
        color: #fff;
        font-size: 32px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .close-modal:hover {
        color: #ff7f50;
    }
    
    @keyframes zoomIn {
        from {
            transform: scale(0.8);
            opacity: 0;
        }
        to {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    /* Flash Messages */
    .flash-messages {
        margin-bottom: 24px;
    }
    
    .flash-message {
        padding: 14px 20px;
        border-radius: 10px;
        margin-bottom: 12px;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .flash-message.success {
        background: rgba(76, 217, 100, 0.15);
        border: 1px solid rgba(76, 217, 100, 0.3);
        color: #4cd964;
    }
    
    .flash-message.danger {
        background: rgba(255, 107, 107, 0.15);
        border: 1px solid rgba(255, 107, 107, 0.3);
        color: #ff6b6b;
    }
    
    .flash-message.info {
        background: rgba(64, 156, 255, 0.15);
        border: 1px solid rgba(64, 156, 255, 0.3);
        color: #409cff;
    }
    
    /* Empty State */
    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: rgba(255, 255, 255, 0.5);
    }
    
    .empty-state i {
        font-size: 64px;
        margin-bottom: 16px;
        opacity: 0.3;
    }
    
    /* Badge */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    
    .badge-orange {
        background: rgba(255, 127, 80, 0.2);
        color: #ff7f50;
    }
    
    .badge-blue {
        background: rgba(64, 156, 255, 0.2);
        color: #409cff;
    }
    
    /* Date Range Buttons */
    .date-range-buttons {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
    }
    
    .date-btn {
        padding: 8px 20px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.7);
        cursor: pointer;
        transition: all 0.3s ease;
        font-size: 13px;
        font-weight: 500;
    }
    
    .date-btn:hover {
        background: rgba(255, 255, 255, 0.08);
        color: #ffffff;
    }
    
    .date-btn.active {
        background: linear-gradient(135deg, #ff7f50 0%, #ff6b45 100%);
        color: #ffffff;
        border-color: transparent;
    }
    
    /* ============================================
       RESPONSIVE DESIGN - MOBILE & TABLET
       ============================================ */
    
    /* Tablet View (768px - 1024px) */
    @media (max-width: 1024px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        
        .form-grid {
            grid-template-columns: 1fr;
        }
        
        .image-gallery {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    /* Mobile View (up to 768px) - CRITICAL SECTION */
    @media (max-width: 768px) {
        body {
            overflow-x: hidden;
        }
        
        /* Show hamburger button */
        .mobile-menu-btn {
            display: flex !important;
        }
        
        /* Hide sidebar by default (slide off-screen) */
        .sidebar {
            transform: translateX(-100%);
        }
        
        /* Show sidebar when open */
        .sidebar.open {
            transform: translateX(0);
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.5);
        }
        
        /* Show overlay when sidebar is open */
        .sidebar-overlay.active {
            display: block;
        }
        
        /* Main content takes full width */
        .main-content {
            margin-left: 0 !important;
            width: 100% !important;
            padding: 80px 16px 20px 16px;
        }
        
        /* Adjust page header */
        .page-header {
            margin-bottom: 24px;
            padding-bottom: 16px;
        }
        
        .page-title {
            font-size: 24px;
        }
        
        .page-subtitle {
            font-size: 13px;
        }
        
        /* Stats grid becomes single column */
        .stats-grid {
            grid-template-columns: 1fr;
            gap: 16px;
        }
        
        .stat-card {
            padding: 20px;
        }
        
        .stat-value {
            font-size: 28px;
        }
        
        /* Chart containers */
        .chart-container {
            padding: 20px;
        }
        
        .chart-header {
            flex-direction: column;
            align-items: flex-start;
        }
        
        .chart-title {
            font-size: 16px;
        }
        
        /* Date range buttons stack */
        .date-range-buttons {
            width: 100%;
        }
        
        .date-btn {
            flex: 1;
            min-width: 80px;
            padding: 8px 12px;
            font-size: 12px;
        }
        
        /* Table container */
        .table-container {
            padding: 16px;
        }
        
        table {
            font-size: 13px;
        }
        
        th, td {
            padding: 10px 8px;
        }
        
        /* Image gallery becomes single column */
        .image-gallery {
            grid-template-columns: 1fr;
        }
        
        .image-card img {
            height: 180px;
        }
        
        /* Form adjustments */
        .form-container {
            padding: 20px;
        }
        
        .form-grid {
            grid-template-columns: 1fr;
            gap: 16px;
        }
        
        /* Filter bar */
        .filter-bar {
            flex-direction: column;
            align-items: stretch;
        }
        
        .filter-bar select {
            width: 100%;
            min-width: unset;
        }
        
        /* Buttons */
        .btn {
            width: 100%;
            text-align: center;
            padding: 14px 20px;
        }
        
        /* Modal adjustments */
        .modal-content {
            margin: 10% 20px;
            max-width: calc(100% - 40px);
        }
        
        .close-modal {
            top: -35px;
            font-size: 28px;
        }
        
        /* Image thumbs in table */
        .image-thumb {
            width: 80px;
            height: 60px;
        }
    }
    
    /* Extra small devices */
    @media (max-width: 480px) {
        .mobile-menu-btn {
            top: 15px;
            left: 15px;
            width: 44px;
            height: 44px;
            font-size: 24px;
        }
        
        .main-content {
            padding: 70px 12px 16px 12px;
        }
        
        .page-title {
            font-size: 20px;
        }
        
        .stat-icon {
            width: 48px;
            height: 48px;
            font-size: 20px;
        }
        
        .stat-value {
            font-size: 24px;
        }
        
        .chart-container,
        .table-container,
        .form-container {
            padding: 16px;
        }
        
        .date-btn {
            font-size: 11px;
            padding: 6px 10px;
        }
    }
</style>
"""
# Shared Scripts
SHARED_SCRIPTS = """
<script>
// Sidebar toggle for mobile
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
}

// Close sidebar when clicking overlay
function closeSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
}

// Close sidebar when clicking any menu item (mobile only)
document.addEventListener('DOMContentLoaded', function() {
    const menuItems = document.querySelectorAll('.menu-item');
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        menuItems.forEach(item => {
            item.addEventListener('click', function() {
                setTimeout(closeSidebar, 150);
            });
        });
    }
});

// Image modal functions
function openModal(imageSrc) {
    document.getElementById('imageModal').style.display = 'block';
    document.getElementById('modalImage').src = imageSrc;
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    document.getElementById('imageModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

window.onclick = function(event) {
    const modal = document.getElementById('imageModal');
    if (event.target == modal) {
        closeModal();
    }
}

// Close modal on escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// Clipboard copy helper (device keys)
function copyDeviceKey(el) {
    const key = el.getAttribute('data-key');
    if (!key) return;
    
    navigator.clipboard.writeText(key).then(() => {
        const toast = document.createElement('div');
        toast.innerText = '✓ Device key copied!';
        toast.style.cssText = `
            position: fixed;
            z-index: 9999;
            right: 20px;
            bottom: 20px;
            padding: 12px 20px;
            background: rgba(76, 217, 100, 0.9);
            color: #fff;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            animation: slideInUp 0.3s ease;
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.style.animation = 'slideOutDown 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    }).catch(err => {
        alert('Failed to copy: ' + err);
    });
}

// Add toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInUp {
        from {
            transform: translateY(100%);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutDown {
        from {
            transform: translateY(0);
            opacity: 1;
        }
        to {
            transform: translateY(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
</script>
"""

# LOGIN TEMPLATE
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - JP Global InsectDetect</title>
    <link rel="manifest" href="/static/manifest.json">
    <link rel="icon" type="image/x-icon" href="/favicon.ico">
    <meta name="theme-color" content="#ff7f50">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .login-container {
            width: 90%;
            max-width: 450px;
        }
        
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 48px 40px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }
        
        .logo-container {
            text-align: center;
            margin-bottom: 32px;
        }
        
        .logo-container img {
            width: 200px;
            margin-bottom: 16px;
        }
        
        .welcome-text {
            color: #ffffff;
            font-size: 28px;
            font-weight: 600;
            text-align: center;
            margin-bottom: 12px;
            background: linear-gradient(135deg, #ff7f50 0%, #409cff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .subtitle {
            color: rgba(255, 255, 255, 0.6);
            text-align: center;
            font-size: 14px;
            margin-bottom: 32px;
        }
        
        .form-group {
            margin-bottom: 24px;
        }
        
        .form-group label {
            display: block;
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .form-group input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #ffffff;
            font-size: 15px;
            font-family: 'Poppins', sans-serif;
        }
        
        .form-group input:focus {
            outline: none;
            background: rgba(255, 255, 255, 0.08);
            border-color: #ff7f50;
            box-shadow: 0 0 0 3px rgba(255, 127, 80, 0.1);
        }
        
        .btn-login {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #ff7f50 0%, #ff6b45 100%);
            border: none;
            border-radius: 12px;
            color: #ffffff;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Poppins', sans-serif;
            margin-top: 8px;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 127, 80, 0.4);
        }
        
        .flash-message {
            background: rgba(255, 107, 107, 0.15);
            border: 1px solid rgba(255, 107, 107, 0.3);
            color: #ff6b6b;
            padding: 12px 16px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .credentials-info {
            margin-top: 28px;
            padding-top: 24px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .credentials-info p {
            color: rgba(255, 255, 255, 0.5);
            font-size: 12px;
            text-align: center;
            margin-bottom: 8px;
        }
        
        .cred-box {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 10px 14px;
            margin: 6px 0;
            font-size: 13px;
            color: rgba(255, 255, 255, 0.7);
        }
        
        .cred-box strong {
            color: #ff7f50;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="glass-card">
            <div class="logo-container">
                <img src="/static/images/logo.png" alt="JP Global">
            </div>
            
            <h1 class="welcome-text">Welcome Back</h1>
            <p class="subtitle">Sign in to continue to InsectDetect</p>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-message">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required>
                </div>
                
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                
                <button type="submit" class="btn-login">
                    <i class="fas fa-sign-in-alt"></i> Sign In
                </button>
            </form>
            
            <div class="credentials-info">
                <p>Demo Credentials:</p>
                <div class="cred-box">
                    <strong>Admin:</strong> admin / admin123
                </div>
                <div class="cred-box">
                    <strong>Farmer:</strong> farmer1 / pass123
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# === ADMIN TEMPLATES ===

def admin_sidebar(active_page):
    return f"""
    <!-- Mobile Menu Button -->
    <i class="fas fa-bars mobile-menu-btn" onclick="toggleSidebar()"></i>
    
    <!-- Sidebar Overlay -->
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    
    <!-- Sidebar -->
    <div class="sidebar">
        <div class="sidebar-logo">
            <img src="/static/images/logo.png" alt="JP Global">
            <div class="sidebar-title">Admin Dashboard</div>
        </div>
        <div class="sidebar-menu">
            <a href="/admin/overview" class="menu-item {'active' if active_page == 'overview' else ''}">
                <i class="fas fa-th-large"></i>
                <span>Overview</span>
            </a>
            <a href="/admin/devices" class="menu-item {'active' if active_page == 'devices' else ''}">
                <i class="fas fa-microchip"></i>
                <span>Device Management</span>
            </a>
            <a href="/admin/dataset" class="menu-item {'active' if active_page == 'dataset' else ''}">
                <i class="fas fa-database"></i>
                <span>Dataset</span>
            </a>
            <a href="/admin/images" class="menu-item {'active' if active_page == 'images' else ''}">
                <i class="fas fa-images"></i>
                <span>Images</span>
            </a>
            <a href="/admin/users" class="menu-item {'active' if active_page == 'users' else ''}">
                <i class="fas fa-users"></i>
                <span>User Management</span>
            </a>
            <a href="/logout" class="menu-item logout">
                <i class="fas fa-sign-out-alt"></i>
                <span>Logout</span>
            </a>
        </div>
    </div>
    """

ADMIN_OVERVIEW_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Overview - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    """ + SIDEBAR_STYLES + """
</head>
<body>
    """ + admin_sidebar('overview') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">Overview</h1>
            <p class="page-subtitle">Global platform statistics and insights</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon orange">
                    <i class="fas fa-bug"></i>
                </div>
                <div class="stat-label">Total Detections</div>
                <div class="stat-value">{{ total_detections }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon blue">
                    <i class="fas fa-microchip"></i>
                </div>
                <div class="stat-label">Active Devices</div>
                <div class="stat-value">{{ total_devices }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon green">
                    <i class="fas fa-users"></i>
                </div>
                <div class="stat-label">Total Farmers</div>
                <div class="stat-value">{{ total_farmers }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon purple">
                    <i class="fas fa-chart-line"></i>
                </div>
                <div class="stat-label">Total Insects Counted</div>
                <div class="stat-value">{{ total_insects }}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-chart-pie"></i> Global Insect Distribution</h2>
            </div>
            <canvas id="insectPieChart" style="max-height: 350px;"></canvas>
        </div>
    </div>
    
    <script>
        const summaryData = {{ insect_summary|tojson }};
        
        const pieCtx = document.getElementById('insectPieChart').getContext('2d');
        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: summaryData.map(item => item.insect),
                datasets: [{
                    data: summaryData.map(item => item.count),
                    backgroundColor: [
                        'rgba(255, 127, 80, 0.8)',
                        'rgba(64, 156, 255, 0.8)',
                        'rgba(76, 217, 100, 0.8)',
                        'rgba(175, 82, 222, 0.8)',
                        'rgba(255, 204, 0, 0.8)'
                    ],
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: 'rgba(255, 255, 255, 0.8)',
                            padding: 15,
                            font: { size: 13, family: 'Poppins' }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

ADMIN_DEVICES_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Device Management - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """ + SIDEBAR_STYLES + """
</head>
<body>
    """ + admin_sidebar('devices') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">Device Management</h1>
            <p class="page-subtitle">Manage IoT devices and generate access keys</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash-message {{ category }}">
                            <i class="fas fa-{% if category == 'success' %}check-circle{% elif category == 'danger' %}exclamation-circle{% else %}info-circle{% endif %}"></i>
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <div class="form-container">
            <h2 class="chart-title"><i class="fas fa-plus-circle"></i> Create New Device</h2>
            <form method="POST" action="/admin/create_device">
                <div class="form-grid">
                    <div class="form-group">
                        <label>Device Name</label>
                        <input type="text" name="device_name" required placeholder="e.g., Field Sensor #1">
                    </div>
                    <div class="form-group">
                        <label>Assign to Farmer</label>
                        <select name="farmer_id" required>
                            <option value="">Select Farmer</option>
                            {% for farmer in farmers %}
                                <option value="{{ farmer[2] }}">{{ farmer[1] }} ({{ farmer[2] }})</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Create Device
                </button>
            </form>
        </div>
        
        <div class="table-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-list"></i> All Devices</h2>
            </div>
            
            {% if devices|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>Device Name</th>
                        <th>Farmer ID</th>
                        <th>Device Key</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for device in devices %}
                    <tr>
                        <td>
                            <a href="/admin/device/{{ device[0] }}/analytics" style="color: #ff7f50; text-decoration: none; font-weight: 600;">
                                <i class="fas fa-microchip"></i> {{ device[1] }}
                            </a>
                        </td>
                        <td>{{ device[3] }}</td>
                        <td>
                            <!-- clickable truncated key that copies full key to clipboard -->
                            <code style="font-size: 12px; color: #409cff; cursor: pointer;"
                                  onclick="copyDeviceKey(this)"
                                  data-key="{{ device[2] }}">
                                {{ device[2][:36] }}... <i class="fas fa-copy" style="margin-left:6px; font-size:11px;"></i>
                            </code>
                        </td>
                        <td>{{ device[4] }}</td>
                        <td>
                            <form method="POST" action="/admin/regenerate_key" style="display: inline;">
                                <input type="hidden" name="device_id" value="{{ device[0] }}">
                                <button type="submit" class="btn btn-secondary" style="padding: 6px 14px; font-size: 12px;">
                                    <i class="fas fa-sync"></i> Regenerate Key
                                </button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <i class="fas fa-microchip"></i>
                <p>No devices yet. Create one above!</p>
            </div>
            {% endif %}
        </div>
    </div>

    """ + SHARED_SCRIPTS + """
</body>
</html>
"""

ADMIN_DEVICE_ANALYTICS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Device Analytics - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    """ + SIDEBAR_STYLES + """
</head>
<body>
    """ + admin_sidebar('devices') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">{{ device[1] }} Analytics</h1>
            <p class="page-subtitle">Farmer: {{ device[3] }} | Device ID: #{{ device[0] }}</p>
        </div>
        
        <a href="/admin/devices" class="btn btn-secondary" style="margin-bottom: 24px;">
            <i class="fas fa-arrow-left"></i> Back to Devices
        </a>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon orange">
                    <i class="fas fa-bug"></i>
                </div>
                <div class="stat-label">Total Detections</div>
                <div class="stat-value">{{ records|length }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon blue">
                    <i class="fas fa-layer-group"></i>
                </div>
                <div class="stat-label">Insect Types</div>
                <div class="stat-value">{{ summary|length }}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-chart-pie"></i> Insect Distribution</h2>
            </div>
            <canvas id="insectPieChart" style="max-height: 300px;"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-chart-bar"></i> Detection Counts</h2>
            </div>
            <canvas id="insectBarChart" style="max-height: 350px;"></canvas>
        </div>
        
        <div class="table-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-table"></i> Recent Detections</h2>
            </div>
            
            {% if records|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Insect</th>
                        <th>Count</th>
                        <th>Image</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in records[:20] %}
                    <tr>
                        <td>{{ row.timestamp }}</td>
                        <td>{{ row.insect }}</td>
                        <td><span class="badge badge-orange">{{ row.count }}</span></td>
                        <td>
                            {% if row.image_url %}
                                <img src="{{ row.image_url }}" class="image-thumb" onclick="openModal('{{ row.image_url }}')" alt="Detection">
                            {% else %}
                                <span style="color: rgba(255,255,255,0.3);">No image</span>
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No detection records for this device yet</p>
            </div>
            {% endif %}
        </div>
    </div>
    
    <div id="imageModal" class="modal" onclick="closeModal()">
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <img id="modalImage" src="" alt="Full size">
        </div>
    </div>
    
    """ + SHARED_SCRIPTS + """
    
    <script>
        const summaryData = {{ summary|tojson }};
        
        const pieCtx = document.getElementById('insectPieChart').getContext('2d');
        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: summaryData.map(item => item.insect),
                datasets: [{
                    data: summaryData.map(item => item.count),
                    backgroundColor: [
                        'rgba(255, 127, 80, 0.8)',
                        'rgba(64, 156, 255, 0.8)',
                        'rgba(76, 217, 100, 0.8)',
                        'rgba(175, 82, 222, 0.8)',
                        'rgba(255, 204, 0, 0.8)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: 'rgba(255, 255, 255, 0.8)', font: { family: 'Poppins' } }
                    }
                }
            }
        });
        
        const barCtx = document.getElementById('insectBarChart').getContext('2d');
        new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: summaryData.map(item => item.insect),
                datasets: [{
                    label: 'Detection Count',
                    data: summaryData.map(item => item.count),
                    backgroundColor: 'rgba(255, 127, 80, 0.6)',
                    borderColor: 'rgba(255, 127, 80, 1)',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    },
                    x: {
                        ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                        grid: { color: 'rgba(255, 255, 255, 0.05)' }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

# Continue in next message due to length...

ADMIN_DATASET_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dataset - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """ + SIDEBAR_STYLES + """
</head>
<body>
    """ + admin_sidebar('dataset') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">Dataset</h1>
            <p class="page-subtitle">Browse and filter all detection records</p>
        </div>
        
        <div class="filter-bar">
            <i class="fas fa-filter" style="color: rgba(255, 255, 255, 0.5);"></i>
            <select id="farmerFilter" onchange="window.location.href='/admin/dataset?farmer_id=' + this.value">
                <option value="">All Farmers</option>
                {% for farmer in farmers %}
                    <option value="{{ farmer[2] }}" {% if selected_farmer == farmer[2] %}selected{% endif %}>
                        {{ farmer[1] }} ({{ farmer[2] }})
                    </option>
                {% endfor %}
            </select>
        </div>
        
        <div class="table-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-table"></i> Detection Records ({{ records|length }})</h2>
            </div>
            
            {% if records|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Farmer ID</th>
                        <th>Insect Type</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in records %}
                    <tr>
                        <td>{{ row.timestamp }}</td>
                        <td>{{ row.farmer_id }}</td>
                        <td>{{ row.insect }}</td>
                        <td><span class="badge badge-orange">{{ row.count }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <i class="fas fa-database"></i>
                <p>No records found</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

ADMIN_IMAGES_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Images - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """ + SIDEBAR_STYLES + """
    <style>
        .image-preview {
            margin-top: 12px;
            border-radius: 8px;
            max-width: 200px;
            max-height: 150px;
            object-fit: cover;
            border: 2px solid rgba(255, 127, 80, 0.3);
        }
        .image-select-option {
            padding: 8px;
        }
    </style>
</head>
<body>
    """ + admin_sidebar('images') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">Detection Images</h1>
            <p class="page-subtitle">Browse insect detection images</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash-message {{ category }}">
                            <i class="fas fa-{% if category == 'success' %}check-circle{% elif category == 'danger' %}exclamation-circle{% else %}info-circle{% endif %}"></i>
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <!-- IMPROVED FORM - Select from available images -->
        <div class="form-container">
            <h2 class="chart-title"><i class="fas fa-link"></i> Link Images from Supabase Storage</h2>
            <p style="color: rgba(255, 255, 255, 0.6); font-size: 13px; margin-bottom: 16px;">
                Select from {{ available_images|length }} images found in your Supabase storage
            </p>
            
            {% if available_images and available_images|length > 0 %}
            <form method="POST" action="/admin/create_record_for_image">
                <div class="form-grid">
                    <div class="form-group" style="grid-column: 1 / -1;">
                        <label>Select Image</label>
                        <select name="image_url" id="imageSelect" required onchange="previewImage()">
                            <option value="">-- Choose an image --</option>
                            {% for img in available_images %}
                                <option value="{{ img.url }}" data-url="{{ img.url }}">{{ img.filename }}</option>
                            {% endfor %}
                        </select>
                        <img id="imagePreview" class="image-preview" style="display: none;" alt="Preview">
                    </div>
                    <div class="form-group">
                        <label>Farmer ID</label>
                        <select name="farmer_id" required>
                            <option value="">Select Farmer</option>
                            {% for farmer in farmers %}
                                <option value="{{ farmer[2] }}">{{ farmer[1] }} ({{ farmer[2] }})</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Insect Type</label>
                        <select name="insect" required>
                            <option value="whiteflies">Whiteflies</option>
                            <option value="aphids">Aphids</option>
                            <option value="thrips">Thrips</option>
                            <option value="beetle">Beetle</option>
                            <option value="fungus gnats">Fungus Gnats</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Count</label>
                        <input type="number" name="count" value="1" min="1" required>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-link"></i> Create Record for Selected Image
                </button>
            </form>
            {% else %}
            <div class="empty-state">
                <i class="fas fa-folder-open"></i>
                <p>No unlinked images found in Supabase storage</p>
                <small style="color: rgba(255, 255, 255, 0.5);">Upload images to: Storage → insect-images → insects/</small>
            </div>
            {% endif %}
        </div>
        
        <div class="filter-bar">
            <i class="fas fa-filter" style="color: rgba(255, 255, 255, 0.5);"></i>
            <select id="farmerFilter" onchange="window.location.href='/admin/images?farmer_id=' + this.value">
                <option value="">All Farmers</option>
                {% for farmer in farmers %}
                    <option value="{{ farmer[2] }}" {% if selected_farmer == farmer[2] %}selected{% endif %}>
                        {{ farmer[1] }} ({{ farmer[2] }})
                    </option>
                {% endfor %}
            </select>
        </div>
        
        {% if records|length > 0 %}
        <div class="image-gallery">
            {% for row in records %}
            <div class="image-card" onclick="openModal('{{ row.image_url }}')">
                <img src="{{ row.image_url }}" alt="{{ row.insect }}">
                <div class="image-card-info">
                    <div class="image-card-title">{{ row.insect }}</div>
                    <div class="image-card-meta">
                        <i class="fas fa-clock"></i> {{ row.timestamp }}<br>
                        <i class="fas fa-user"></i> {{ row.farmer_id }} | Count: {{ row.count }}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty-state">
            <i class="fas fa-images"></i>
            <p>No linked images found</p>
        </div>
        {% endif %}
    </div>
    
    <div id="imageModal" class="modal" onclick="closeModal()">
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <img id="modalImage" src="" alt="Full size">
        </div>
    </div>
    
    """ + SHARED_SCRIPTS + """
    
    <script>
        function previewImage() {
            const select = document.getElementById('imageSelect');
            const preview = document.getElementById('imagePreview');
            const v = select.options[select.selectedIndex].getAttribute('data-url');
            if (v) {
                preview.src = v;
                preview.style.display = 'block';
            } else {
                preview.style.display = 'none';
            }
        }
    </script>
</body>
</html>
"""
ADMIN_USERS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>User Management - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """ + SIDEBAR_STYLES + """
</head>
<body>
    """ + admin_sidebar('users') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">User Management</h1>
            <p class="page-subtitle">Create and manage farmer accounts</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                <div class="flash-messages">
                    {% for category, message in messages %}
                        <div class="flash-message {{ category }}">
                            <i class="fas fa-{% if category == 'success' %}check-circle{% elif category == 'danger' %}exclamation-circle{% else %}info-circle{% endif %}"></i>
                            {{ message }}
                        </div>
                    {% endfor %}
                </div>
            {% endif %}
        {% endwith %}
        
        <div class="form-container">
            <h2 class="chart-title"><i class="fas fa-user-plus"></i> Create New Farmer Account</h2>
            <form method="POST" action="/admin/create_farmer">
                <div class="form-grid">
                    <div class="form-group">
                        <label>Username</label>
                        <input type="text" name="username" required placeholder="e.g., farmer2">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" required placeholder="Secure password">
                    </div>
                    <div class="form-group">
                        <label>Farmer ID</label>
                        <input type="text" name="farmer_id" required placeholder="e.g., farmer_002">
                    </div>
                </div>
                <button type="submit" class="btn btn-primary">
                    <i class="fas fa-user-plus"></i> Create Farmer Account
                </button>
            </form>
        </div>
        
        <div class="table-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-users"></i> All Farmers ({{ farmers|length }})</h2>
            </div>
            
            {% if farmers|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Farmer ID</th>
                    </tr>
                </thead>
                <tbody>
                    {% for farmer in farmers %}
                    <tr>
                        <td>{{ farmer[0] }}</td>
                        <td>{{ farmer[1] }}</td>
                        <td><span class="badge badge-blue">{{ farmer[2] }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <i class="fas fa-users"></i>
                <p>No farmers yet</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# === FARMER TEMPLATES ===

def farmer_sidebar(active_page):
    return f"""
    <!-- Mobile Menu Button -->
    <i class="fas fa-bars mobile-menu-btn" onclick="toggleSidebar()"></i>
    
    <!-- Sidebar Overlay -->
    <div class="sidebar-overlay" onclick="closeSidebar()"></div>
    
    <!-- Sidebar -->
    <div class="sidebar">
        <div class="sidebar-logo">
            <img src="/static/images/logo.png" alt="JP Global">
            <div class="sidebar-title">Farmer Dashboard</div>
        </div>
        <div class="sidebar-menu">
            <a href="/farmer/overview" class="menu-item {'active' if active_page == 'overview' else ''}">
                <i class="fas fa-th-large"></i>
                <span>Overview</span>
            </a>
            <a href="/farmer/analysis" class="menu-item {'active' if active_page == 'analysis' else ''}">
                <i class="fas fa-chart-line"></i>
                <span>Analysis</span>
            </a>
            <a href="/farmer/dataset" class="menu-item {'active' if active_page == 'dataset' else ''}">
                <i class="fas fa-database"></i>
                <span>Dataset</span>
            </a>
            <a href="/farmer/images" class="menu-item {'active' if active_page == 'images' else ''}">
                <i class="fas fa-images"></i>
                <span>Images</span>
            </a>
            <a href="/logout" class="menu-item logout">
                <i class="fas fa-sign-out-alt"></i>
                <span>Logout</span>
            </a>
        </div>
    </div>
    """
FARMER_OVERVIEW_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Overview - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    """ + SIDEBAR_STYLES + """
</head>
<body>
    """ + farmer_sidebar('overview') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">Overview</h1>
            <p class="page-subtitle">Farm ID: {{ farmer_id }}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon orange">
                    <i class="fas fa-bug"></i>
                </div>
                <div class="stat-label">Total Detections</div>
                <div class="stat-value">{{ total_detections }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon blue">
                    <i class="fas fa-chart-bar"></i>
                </div>
                <div class="stat-label">Total Insect Count</div>
                <div class="stat-value">{{ total_count }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon green">
                    <i class="fas fa-trophy"></i>
                </div>
                <div class="stat-label">Highest Insect</div>
                <div class="stat-value" style="font-size: 20px;">{{ top_insect }}</div>
            </div>
            
            <div class="stat-card">
                <div class="stat-icon purple">
                    <i class="fas fa-hashtag"></i>
                </div>
                <div class="stat-label">Highest Count</div>
                <div class="stat-value">{{ top_count }}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-chart-pie"></i> Insect Distribution</h2>
            </div>
            <canvas id="insectPieChart" style="max-height: 350px;"></canvas>
        </div>
    </div>
    
    <script>
        const summaryData = {{ insect_summary|tojson }};
        
        const pieCtx = document.getElementById('insectPieChart').getContext('2d');
        new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: summaryData.map(item => item.insect),
                datasets: [{
                    data: summaryData.map(item => item.count),
                    backgroundColor: [
                        'rgba(255, 127, 80, 0.8)',
                        'rgba(64, 156, 255, 0.8)',
                        'rgba(76, 217, 100, 0.8)',
                        'rgba(175, 82, 222, 0.8)',
                        'rgba(255, 204, 0, 0.8)'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: 'rgba(255, 255, 255, 0.8)', font: { family: 'Poppins' } }
                    }
                }
            }
        });
    </script>
</body>
</html>
"""

FARMER_ANALYSIS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    """ + SIDEBAR_STYLES + """
</head>
<body>
    """ + farmer_sidebar('analysis') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">Analysis</h1>
            <p class="page-subtitle">Detailed insect detection trends and patterns</p>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-chart-bar"></i> Detection Summary</h2>
                <div class="date-range-buttons">
                    <button class="date-btn active" onclick="loadData(7, this)">Last 7 Days</button>
                    <button class="date-btn" onclick="loadData(30, this)">Last 30 Days</button>
                    <button class="date-btn" onclick="loadData(365, this)">Last 365 Days</button>
                </div>
            </div>
            <canvas id="barChart" style="max-height: 350px;"></canvas>
        </div>
        
        <div class="chart-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-chart-line"></i> Daily Trends</h2>
            </div>
            <canvas id="lineChart" style="max-height: 400px;"></canvas>
        </div>
    </div>
    
    <script>
        let barChart, lineChart;
        const farmerId = "{{ farmer_id }}";
        
        async function loadData(days, button) {
            // Update active button
            document.querySelectorAll('.date-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Fetch data
            const response = await fetch(`/api/analysis_data?farmer_id=${farmerId}&days=${days}`);
            const data = await response.json();
            
            // Update Bar Chart
            console.log('Destroying old chart...');
            if (barChart) barChart.destroy();
            const barCtx = document.getElementById('barChart').getContext('2d');
            barChart = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: data.labels || [],
                    datasets: [{
                        label: 'Total Count',
                        data: data.bar_data || [],
                        label: 'Total Count',
                        labels: [...data.labels],
                        backgroundColor: 'rgba(255, 127, 80, 0.6)',
                        borderColor: 'rgba(255, 127, 80, 1)',
                        borderWidth: 2,
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        },
                        x: {
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        }
                    },
                    plugins: {
                        legend: { labels: { color: 'rgba(255, 255, 255, 0.8)' } }
                    }
                }
            });
            
            // Update Line Chart
            if (lineChart) lineChart.destroy();
            const lineCtx = document.getElementById('lineChart').getContext('2d');
            lineChart = new Chart(lineCtx, {
                type: 'line',
                data: {
                    labels: data.line_labels,
                    datasets: data.line_datasets
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { color: 'rgba(255, 255, 255, 0.7)' },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        },
                        x: {
                            ticks: { color: 'rgba(255, 255, 255, 0.7)', maxRotation: 45, minRotation: 45 },
                            grid: { color: 'rgba(255, 255, 255, 0.05)' }
                        }
                    },
                    plugins: {
                        legend: { 
                            position: 'top',
                            labels: { color: 'rgba(255, 255, 255, 0.8)', font: { family: 'Poppins' } }
                        }
                    }
                }
            });
        }
        
        // Load initial data (7 days)
        window.addEventListener('load', () => {
            const activeBtn = document.querySelector('.date-btn.active');
            loadData(7, activeBtn);
        });
    </script>
</body>
</html>
"""

FARMER_DATASET_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dataset - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """ + SIDEBAR_STYLES + """
</head>
<body>
    """ + farmer_sidebar('dataset') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">Dataset</h1>
            <p class="page-subtitle">Browse your detection records</p>
        </div>
        
        <div class="filter-bar">
            <i class="fas fa-filter" style="color: rgba(255, 255, 255, 0.5);"></i>
            <select id="deviceFilter" onchange="window.location.href='/farmer/dataset?device_id=' + this.value">
                <option value="">All Devices</option>
                {% for device in devices %}
                    <option value="{{ device[0] }}" {% if selected_device == device[0]|string %}selected{% endif %}>
                        {{ device[1] }}
                    </option>
                {% endfor %}
            </select>
        </div>
        
        <div class="table-container">
            <div class="chart-header">
                <h2 class="chart-title"><i class="fas fa-table"></i> Detection Records ({{ records|length }})</h2>
            </div>
            
            {% if records|length > 0 %}
            <table>
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>Insect Type</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in records %}
                    <tr>
                        <td>{{ row.timestamp }}</td>
                        <td>{{ row.insect }}</td>
                        <td><span class="badge badge-orange">{{ row.count }}</span></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <div class="empty-state">
                <i class="fas fa-database"></i>
                <p>No records found</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

FARMER_IMAGES_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Images - JP Global InsectDetect</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    """ + SIDEBAR_STYLES + """
</head>
<body>
    """ + farmer_sidebar('images') + """
    
    <div class="main-content">
        <div class="page-header">
            <h1 class="page-title">Detection Images</h1>
            <p class="page-subtitle">Browse your insect detection images</p>
        </div>
        
        <div class="filter-bar">
            <i class="fas fa-filter" style="color: rgba(255, 255, 255, 0.5);"></i>
            <select id="deviceFilter" onchange="window.location.href='/farmer/images?device_id=' + this.value">
                <option value="">All Devices</option>
                {% for device in devices %}
                    <option value="{{ device[0] }}" {% if selected_device == device[0]|string %}selected{% endif %}>
                        {{ device[1] }}
                    </option>
                {% endfor %}
            </select>
        </div>
        
        {% if records|length > 0 %}
        <div class="image-gallery">
            {% for row in records %}
            <div class="image-card" onclick="openModal('{{ row.image_url }}')">
                <img src="{{ row.image_url }}" alt="{{ row.insect }}">
                <div class="image-card-info">
                    <div class="image-card-title">{{ row.insect }}</div>
                    <div class="image-card-meta">
                        <i class="fas fa-clock"></i> {{ row.timestamp }}<br>
                        <i class="fas fa-hashtag"></i> Count: {{ row.count }}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty-state">
            <i class="fas fa-images"></i>
            <p>No images found</p>
        </div>
        {% endif %}
    </div>
    
    <div id="imageModal" class="modal" onclick="closeModal()">
        <div class="modal-content">
            <span class="close-modal">&times;</span>
            <img id="modalImage" src="" alt="Full size">
        </div>
    </div>
    
    """ + SHARED_SCRIPTS + """
</body>
</html>
"""
