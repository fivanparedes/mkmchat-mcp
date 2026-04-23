<?php

namespace App\Models;

// use Illuminate\Contracts\Auth\MustVerifyEmail;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    /** @use HasFactory<\Database\Factories\UserFactory> */
    use HasFactory, Notifiable;

    protected $fillable = [
        'name',
        'email',
        'password',
        'role',
        'bio',
        'avatar_url',
        'theme',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
        ];
    }

    /**
     * Check whether the user has admin privileges.
     */
    public function isAdmin(): bool
    {
        return $this->role === 'admin';
    }

    public function queryHistories(): HasMany
    {
        return $this->hasMany(QueryHistory::class);
    }

    public function conversations(): HasMany
    {
        return $this->hasMany(Conversation::class);
    }

    public function todayQueryCount(): int
    {
        $queryHistoryCount = $this->queryHistories()
            ->whereDate('created_at', today())
            ->count();

        $chatCount = ConversationMessage::query()
            ->whereHas('conversation', fn ($query) => $query->where('user_id', $this->id))
            ->where('role', 'user')
            ->whereDate('created_at', today())
            ->count();

        return $queryHistoryCount + $chatCount;
    }
}
