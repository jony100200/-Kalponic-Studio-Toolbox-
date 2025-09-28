"""
✨ UI Animation System
======================
Role: Animation coordinator for smooth transitions
SOLID: Single responsibility for UI animations
"""

from PySide6.QtCore import QObject, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PySide6.QtGui import QPainter


class UIAnimator(QObject):
    """
    ✨ UI Animation Manager
    =======================
    Role: Animation Coordinator - Handles all UI transitions
    Pattern: Centralized animation management
    """
    
    def __init__(self):
        super().__init__()
        self.active_animations = []
        self.animation_frame = 0
    
    def fade_in_widget(self, widget: QWidget, duration: int = 500):
        """🌅 Fade in animation for widgets"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.active_animations.append(animation)
        animation.start()
        
        return animation
    
    def fade_out_widget(self, widget: QWidget, duration: int = 300):
        """🌇 Fade out animation for widgets"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.InCubic)
        
        self.active_animations.append(animation)
        animation.start()
        
        return animation
    
    def slide_in_widget(self, widget: QWidget, direction='left', duration: int = 400):
        """➡️ Slide in animation for widgets"""
        geometry = widget.geometry()
        
        if direction == 'left':
            start_pos = geometry.translated(-geometry.width(), 0)
        elif direction == 'right':
            start_pos = geometry.translated(geometry.width(), 0)
        elif direction == 'up':
            start_pos = geometry.translated(0, -geometry.height())
        else:  # down
            start_pos = geometry.translated(0, geometry.height())
        
        widget.setGeometry(start_pos)
        
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setStartValue(start_pos)
        animation.setEndValue(geometry)
        animation.setEasingCurve(QEasingCurve.OutQuart)
        
        self.active_animations.append(animation)
        animation.start()
        
        return animation
    
    def pulse_animation(self, widget: QWidget, scale_factor: float = 1.1, duration: int = 600):
        """💓 Pulse animation for attention-grabbing"""
        # Create scale animation (simplified - would need transform in real implementation)
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setKeyValueAt(0.5, 0.7)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutSine)
        animation.setLoopCount(2)  # Pulse twice
        
        self.active_animations.append(animation)
        animation.start()
        
        return animation
    
    def setup_panel_transitions(self, panel: QWidget):
        """🎭 Setup hover and interaction animations for panels"""
        # Add hover effects and smooth transitions
        panel.setStyleSheet(panel.styleSheet() + """
        QWidget {
            transition: all 0.3s ease;
        }
        
        QWidget:hover {
            background-color: rgba(0, 212, 170, 0.05);
        }
        
        QPushButton {
            transition: all 0.2s ease;
        }
        
        QPushButton:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3);
        }
        """)
    
    def setup_loading_spinner(self, widget: QWidget):
        """🌀 Create loading spinner animation"""
        # Simplified spinner - would use custom painting in real implementation
        animation = QPropertyAnimation(widget, b"rotation")
        animation.setDuration(1000)
        animation.setStartValue(0)
        animation.setEndValue(360)
        animation.setLoopCount(-1)  # Infinite loop
        animation.setEasingCurve(QEasingCurve.Linear)
        
        self.active_animations.append(animation)
        animation.start()
        
        return animation
    
    def animate_progress_bar(self, progress_bar, target_value: int, duration: int = 1000):
        """📈 Smooth progress bar animation"""
        current_value = progress_bar.value()
        
        animation = QPropertyAnimation(progress_bar, b"value")
        animation.setDuration(duration)
        animation.setStartValue(current_value)
        animation.setEndValue(target_value)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        
        self.active_animations.append(animation)
        animation.start()
        
        return animation
    
    def animate_number_counter(self, label, target_number: float, duration: int = 800):
        """🔢 Animate number changes smoothly"""
        # Custom animation for number counting
        start_value = 0
        try:
            start_value = float(label.text().replace('%', '').replace('GB', '').replace('tok/s', '').strip())
        except:
            start_value = 0
        
        def update_number(value):
            if 'GB' in label.text():
                label.setText(f"{value:.1f} GB")
            elif '%' in label.text():
                label.setText(f"{int(value)}%")
            elif 'tok/s' in label.text():
                label.setText(f"{int(value)} tok/s")
            else:
                label.setText(f"{value:.1f}")
        
        # Create custom property animation (simplified)
        timer = QTimer()
        steps = duration // 16  # 60 FPS
        step_size = (target_number - start_value) / steps
        current_step = 0
        
        def animate_step():
            nonlocal current_step
            if current_step < steps:
                current_value = start_value + (step_size * current_step)
                update_number(current_value)
                current_step += 1
            else:
                update_number(target_number)
                timer.stop()
        
        timer.timeout.connect(animate_step)
        timer.start(16)  # 60 FPS
        
        return timer
    
    def create_glow_effect(self, widget: QWidget, glow_color: str = "#00d4aa"):
        """✨ Create glowing border effect"""
        # Simplified glow effect using stylesheet
        glow_style = f"""
        QWidget {{
            border: 2px solid {glow_color};
            border-radius: 8px;
            background-color: rgba({self._hex_to_rgb(glow_color)}, 0.1);
        }}
        """
        
        # Apply glow with fade in/out
        original_style = widget.styleSheet()
        
        # Fade in glow
        widget.setStyleSheet(original_style + glow_style)
        
        # Auto-remove glow after 2 seconds
        QTimer.singleShot(2000, lambda: widget.setStyleSheet(original_style))
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """🎨 Convert hex color to RGB string"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"{rgb[0]}, {rgb[1]}, {rgb[2]}"
    
    def update_frame(self):
        """🎬 Update animation frame (called by timer)"""
        self.animation_frame += 1
        
        # Clean up finished animations
        self.active_animations = [anim for anim in self.active_animations 
                                 if anim.state() == QPropertyAnimation.Running]
    
    def stop_all_animations(self):
        """⏹️ Stop all active animations"""
        for animation in self.active_animations:
            animation.stop()
        self.active_animations.clear()
