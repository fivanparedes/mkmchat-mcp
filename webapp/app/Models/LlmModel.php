<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class LlmModel extends Model
{
    use HasFactory;

    protected $fillable = [
        'name',
        'slug',
        'parameter_size',
        'provider',
        'description',
        'is_active',
    ];

    protected function casts(): array
    {
        return [
            'is_active' => 'boolean',
        ];
    }

    /**
     * Scope: only active models.
     */
    public function scopeActive($query)
    {
        return $query->where('is_active', true);
    }
}
