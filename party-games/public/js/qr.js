// QR code generator helper
const QRHelper = {
  render(containerId, url) {
    const el = document.getElementById(containerId);
    if (!el) return;
    el.innerHTML = '';
    try {
      new QRCode(el, {
        text: url,
        width: 200,
        height: 200,
        colorDark: '#000000',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.M,
      });
    } catch (e) {
      el.textContent = url;
    }
  }
};
