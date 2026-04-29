//  PAGE FADE 
window.addEventListener('load', () => {
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.opacity = '1';
    }, 100);
});

//  3D CARD TILT 
document.querySelectorAll('.box').forEach(card => {
    card.addEventListener('mousemove', e => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        const rotateX = ((y / rect.height) - 0.5) * 10;
        const rotateY = ((x / rect.width) - 0.5) * -10;

        card.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.03)`;
    });

    card.addEventListener('mouseleave', () => {
        card.style.transform = 'rotateX(0) rotateY(0) scale(1)';
    });
});

//  BUTTON RIPPLE 
document.querySelectorAll('.button').forEach(btn => {
    btn.addEventListener('click', function (e) {

        const ripple = document.createElement('span');

        ripple.style.position = 'absolute';
        ripple.style.background = 'rgba(255,255,255,0.4)';
        ripple.style.borderRadius = '50%';
        ripple.style.width = ripple.style.height = '100px';
        ripple.style.left = `${e.offsetX - 50}px`;
        ripple.style.top = `${e.offsetY - 50}px`;
        ripple.style.animation = 'ripple 0.6s linear';

        this.style.position = 'relative';
        this.appendChild(ripple);

        setTimeout(() => ripple.remove(), 600);
    });
});

//  CHAT AUTO SCROLL 
const chatBox = document.getElementById('chat-box');

if (chatBox) {
    const observer = new MutationObserver(() => {
        chatBox.scrollTop = chatBox.scrollHeight;
    });

    observer.observe(chatBox, { childList: true });
}