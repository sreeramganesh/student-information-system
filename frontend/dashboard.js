// ============================================================
// Shared dashboard behavior: nav switching, mobile sidebar, toast
// ============================================================

function initDashboard(){
  // View switching
  const navItems = document.querySelectorAll('.nav-item');
  const views = document.querySelectorAll('.view');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const target = item.dataset.view;
      navItems.forEach(n => n.classList.remove('active'));
      item.classList.add('active');
      views.forEach(v => v.classList.remove('active'));
      const targetView = document.getElementById('view-' + target);
      if (targetView) targetView.classList.add('active');
      closeSidebar();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  });

  // Mobile sidebar toggle
  const hamburger = document.getElementById('hamburger');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sbOverlay');

  function openSidebar(){
    sidebar.classList.add('open');
    overlay.classList.add('show');
  }
  function closeSidebar(){
    sidebar.classList.remove('open');
    overlay.classList.remove('show');
  }

  if (hamburger){
    hamburger.addEventListener('click', openSidebar);
  }
  if (overlay){
    overlay.addEventListener('click', closeSidebar);
  }

  window.closeSidebar = closeSidebar;
}

function showToast(msg){
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2600);
}

document.addEventListener('DOMContentLoaded', initDashboard);
