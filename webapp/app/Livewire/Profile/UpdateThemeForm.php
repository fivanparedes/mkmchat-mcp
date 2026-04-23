<?php

namespace App\Livewire\Profile;

use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Session;
use Illuminate\Validation\Rule;
use Livewire\Component;

class UpdateThemeForm extends Component
{
    public string $theme = 'scorpion';

    public function mount(): void
    {
        $this->theme = Auth::user()->theme ?? 'scorpion';
    }

    public function updateTheme(): void
    {
        $this->validate([
            'theme' => ['required', 'string', Rule::in(['scorpion', 'sub-zero'])],
        ]);

        Auth::user()->update([
            'theme' => $this->theme,
        ]);

        Session::flash('status', 'theme-updated');
        
        // We dispatch an event so we could potentially react to it on the frontend 
        // if needed, or simply let the page reload to apply the theme. 
        // A full page reload is easiest to ensure all styles apply.
        $this->redirect(route('profile', absolute: false), navigate: true);
    }

    public function render()
    {
        return view('livewire.profile.update-theme-form');
    }
}
