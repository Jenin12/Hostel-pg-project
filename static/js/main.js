// Room & PG Rental System - Interactive Helpers

document.addEventListener('DOMContentLoaded', () => {
    // Dismiss modals when clicking on background or pressing Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('[id$="Modal"]').forEach(m => m.classList.add('hidden'));
        }
    });

    document.querySelectorAll('[id$="Modal"]').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
    });
});
