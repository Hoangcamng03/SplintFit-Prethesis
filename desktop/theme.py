"""Modern clinical light QSS theme for SplintFit Studio Desktop."""

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

QPushButton.stepPill {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 14px;
    padding: 6px 11px;
    font-size: 12px;
    font-weight: 500;
    color: #64748B;
}

QPushButton.stepPill:hover {
    background-color: #F8FAFC;
    color: #0F172A;
}

QPushButton.stepPill[active="true"] {
    background-color: #CCFBF1;
    border-color: #99F6E4;
    color: #0F766E;
    font-weight: 700;
}

QPushButton.stepPill[done="true"] {
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
    border: 1px solid #E2E8F0;
    border-radius: 10px;
}

QFrame.card {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 11px;
}

QLabel.stepTag {
    color: #0F766E;
    font-size: 11px;
    font-weight: 700;
    background: transparent;
}

QLabel.stepTitle {
    font-size: 17px;
    font-weight: 700;
    color: #0F172A;
    background: transparent;
}

QLabel.cardTitle {
    font-size: 13px;
    font-weight: 700;
    color: #0F172A;
    background: transparent;
}

QLabel.muted {
    font-size: 12px;
    color: #64748B;
    background: transparent;
}

QLabel.metricPill {
    background-color: #F0FDFA;
    border: 1px solid #99F6E4;
    border-radius: 8px;
    padding: 7px 10px;
    color: #115E59;
    font-size: 12px;
    font-weight: 600;
}

QLabel.statusBanner {
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: 600;
}

QLabel.statusBanner[kind="info"] {
    background-color: #EFF6FF;
    border: 1px solid #BFDBFE;
    color: #1E40AF;
}

QLabel.statusBanner[kind="success"] {
    background-color: #F0FDF4;
    border: 1px solid #86EFAC;
    color: #166534;
}

QLabel.statusBanner[kind="error"] {
    background-color: #FEF2F2;
    border: 1px solid #FCA5A5;
    color: #991B1B;
}

QFrame.statBox {
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
    border-color: #0F766E;
    color: #FFFFFF;
    padding: 9px 16px;
}

QPushButton#primaryBtn:hover {
    background-color: #0D625B;
}

QPushButton.secondaryBtn {
    background-color: #E0F2FE;
    border-color: #BAE6FD;
    color: #0369A1;
}

QPushButton.secondaryBtn:hover {
    background-color: #BAE6FD;
}

QPushButton.presetCard {
    background-color: #FFFFFF;
    border: 1.5px solid #E2E8F0;
    border-radius: 9px;
    padding: 9px 8px;
    text-align: left;
    font-weight: 600;
    font-size: 12px;
    color: #0F172A;
}

QPushButton.presetCard:hover {
    border-color: #5EEAD4;
    background-color: #F0FDFA;
}

QPushButton.presetCard:checked {
    border-color: #0F766E;
    background-color: #F0FDFA;
    color: #0F766E;
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
    background: #E2E8F0;
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
    background: #14B8A6;
    border-radius: 3px;
}

QScrollArea {
    border: none;
    background-color: #FFFFFF;
}

QCheckBox {
    spacing: 6px;
    background: transparent;
    font-weight: 500;
}

QToolButton.accordionBtn {
    background-color: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 8px 10px;
    font-weight: 700;
    color: #0F172A;
    text-align: left;
}
"""
