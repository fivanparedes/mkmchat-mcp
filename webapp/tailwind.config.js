import defaultTheme from 'tailwindcss/defaultTheme';
import forms from '@tailwindcss/forms';

export default {
    content: [
        './vendor/laravel/framework/src/Illuminate/Pagination/resources/views/*.blade.php',
        './storage/framework/views/*.php',
        './resources/views/**/*.blade.php',
    ],

    theme: {
        extend: {
            fontFamily: {
                sans: ['Figtree', ...defaultTheme.fontFamily.sans],
                cinzel: ['Cinzel', 'serif'],
            },
            colors: {
                mk: {
                    bg:           'var(--mk-bg)',
                    surface:      'var(--mk-surface)',
                    card:         'var(--mk-card)',
                    border:       'var(--mk-border)',
                    text:         'var(--mk-text)',
                    muted:        'var(--mk-muted)',
                    fire:         'var(--mk-fire)',
                    'fire-light': 'var(--mk-fire-light)',
                    gold:         'var(--mk-gold)',
                    blood:        'var(--mk-blood)',
                    success:      'var(--mk-success)',
                    danger:       'var(--mk-danger)',
                    'user-text':  'var(--mk-user-text)',
                    'user-muted': 'var(--mk-user-muted)',
                    tag: {
                        'ask-bg':      'var(--mk-tag-ask-bg)',
                        'ask-text':    'var(--mk-tag-ask-text)',
                        'mechanic-bg': 'var(--mk-tag-mechanic-bg)',
                        'mechanic-text': 'var(--mk-tag-mechanic-text)',
                        'team-bg':     'var(--mk-tag-team-bg)',
                        'team-text':   'var(--mk-tag-team-text)',
                        'success-bg':  'var(--mk-tag-success-bg)',
                        'success-text': 'var(--mk-tag-success-text)',
                        'error-bg':    'var(--mk-tag-error-bg)',
                        'error-text':  'var(--mk-tag-error-text)',
                        'pending-bg':  'var(--mk-tag-pending-bg)',
                        'pending-text': 'var(--mk-tag-pending-text)',
                    },
                },
            },
        },
    },

    plugins: [forms],
};
