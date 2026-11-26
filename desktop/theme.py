"""Modern clinical light QSS theme for SplintFit Studio Desktop (valid Qt attribute selectors)."""

STUDIO_QSS = """
QMainWindow, QWidget {
    background-color: #F1F5F9;
    color: #0F172A;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

#topbar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #E2E8F0;
}

#brandLogo {
    background-color: #0F766E;
    color: #FFFFFF;
    border-radius: 9px;
    font-weight: 700;
    font-size: 14px;
    min-width: 34px;
    max-width: 34px;
    min-height: 34px;
    max-height: 34px;
}

#brandTitle {
    font-size: 15px;
    font-weight: 700;
    color: #0F172A;
    background: transparent;
}

#brandSub {
    font-size: 11px;
    color: #64748B;
    background: transparent;
}

#badgePill {
    background-color: #E0F2FE;
    color: #0369A1;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

QPushButton[class="stepPill"] {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 14px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 500;
    color: #64748B;
}

QPushButton[class="stepPill"]:hover {
    background-color: #F1F5F9;
    color: #0F172A;
}

QPushButton[class="stepPill"][active="true"] {
    background-color: #CCFBF1;
    border: 1px solid #5EEAD4;
    color: #0F766E;
    font-weight: 700;
}

QPushButton[class="stepPill"][done="true"] {
    color: #0F766E;
    font-weight: 600;
}

#wizardPanel {
    background-color: #FFFFFF;
    border-left: 1px solid #E2E8F0;
}

#drawerFooter {
    background-color: #FFFFFF;
    border-top: 1px solid #E2E8F0;
}

#viewportToolbar, #layerBar {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 10px;
}

QFrame[class="card"] {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 11px;
}

QLabel[class="stepTag"] {
    color: #0F766E;
    font-size: 11px;
    font-weight: 700;
    background: transparent;
}

QLabel[class="stepTitle"] {
    font-size: 17px;
    font-weight: 700;
    color: #0F172A;
    background: transparent;
}

QLabel[class="cardTitle"] {
    font-size: 13px;
    font-weight: 700;
    color: #0F172A;
    background: transparent;
}

QLabel[class="muted"] {
    font-size: 12px;
    color: #64748B;
    background: transparent;
}

QLabel[class="metricPill"] {
    background-color: #F0FDFA;
    border: 1px solid #99F6E4;
    border-radius: 8px;
    padding: 7px 10px;
    color: #115E59;
    font-size: 12px;
    font-weight: 600;
}

QLabel[class="statusBanner"] {
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 600;
}

QLabel[class="statusBanner"][kind="info"] {
    background-color: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #1E40AF;
}

QLabel[class="statusBanner"][kind="success"] {
    background-color: #F0FDF4;
    border: 1px solid #86EFAC;
    color: #166534;
}

QLabel[class="statusBanner"][kind="error"] {
    background-color: #FEF2F2;
    border: 1px solid #FCA5A5;
    color: #991B1B;
}

QFrame[class="statBox"] {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 9px;
}

QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 7px 13px;
    font-weight: 600;
    color: #0F172A;
}

QPushButton:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
}

QPushButton:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

QPushButton#primaryBtn {
    background-color: #0F766E;
    border: 1px solid #0F766E;
    color: #FFFFFF;
    padding: 9px 18px;
    font-weight: 700;
}

QPushButton#primaryBtn:hover {
    background-color: #0D625B;
}

QPushButton[class="secondaryBtn"] {
    background-color: #E0F2FE;
    border: 1px solid #7DD3FC;
    color: #0369A1;
}

QPushButton[class="secondaryBtn"]:hover {
    background-color: #BAE6FD;
}

QPushButton[class="presetCard"] {
    background-color: #FFFFFF;
    border: 1.5px solid #CBD5E1;
    border-radius: 10px;
    padding: 9px 8px;
    text-align: left;
    font-weight: 600;
    font-size: 12px;
    color: #334155;
}

QPushButton[class="presetCard"]:hover {
    border-color: #2DD4BF;
    background-color: #F0FDFA;
}

QPushButton[class="presetCard"]:checked {
    border: 2px solid #0F766E;
    background-color: #CCFBF1;
    color: #0F766E;
    font-weight: 700;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 7px;
    padding: 5px 8px;
    color: #0F172A;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #0F766E;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #CBD5E1;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #0F766E;
    border: 2px solid #FFFFFF;
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::sub-page:horizontal {
    background: #0D9488;
    border-radius: 3px;
}

QScrollArea {
    border: none;
    background-color: #FFFFFF;
}

QCheckBox {
    spacing: 7px;
    background: transparent;
    font-weight: 600;
    color: #0F172A;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid #94A3B8;
    background-color: #FFFFFF;
}

QCheckBox::indicator:hover {
    border-color: #0F766E;
}

QCheckBox::indicator:checked {
    background-color: #0F766E;
    border-color: #0F766E;
}

QToolButton[class="accordionBtn"] {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 8px 10px;
    font-weight: 700;
    color: #0F172A;
    text-align: left;
}
"""
