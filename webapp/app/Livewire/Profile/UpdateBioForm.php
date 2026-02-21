<?php

namespace App\Livewire\Profile;

use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Session;
use Livewire\Component;

class UpdateBioForm extends Component
{
    public string $bio = '';
    public string $avatarUrl = '';

    public function mount(): void
    {
        $this->bio = Auth::user()->bio ?? '';
        $this->avatarUrl = Auth::user()->avatar_url ?? '';
    }

    public function updateBio(): void
    {
        $this->validate([
            'bio'       => ['nullable', 'string', 'max:500'],
            'avatarUrl' => ['nullable', 'url', 'max:255'],
        ]);

        Auth::user()->update([
            'bio'        => $this->bio,
            'avatar_url' => $this->avatarUrl ?: null,
        ]);

        Session::flash('status', 'bio-updated');
    }

    public function render()
    {
        return view('livewire.profile.update-bio-form');
    }
}
