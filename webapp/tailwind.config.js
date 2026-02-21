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
                    bg:           '#0a0a0a',
                    surface:      '#111111',
                    card:         '#1a1a1a',
                    border:       '#2a2a2a',
                    text:         '#e8e8e8',
                    muted:        '#6b6b6b',
                    fire:         '#e8420a',
                    'fire-light': '#f97316',
                    gold:         '#f59e0b',
                    blood:        '#8b0000',
                },
            },
        },
    },

    plugins: [forms],
};
