<?php

use Illuminate\Support\Facades\Route;

Route::view('/', 'welcome');

Route::middleware(['auth', 'verified'])->group(function () {
    Route::view('dashboard', 'dashboard')->name('dashboard');
    Route::view('history', 'history')->name('history');
    Route::view('ask', 'ask')->name('ask');
});

Route::view('profile', 'profile')
    ->middleware(['auth'])
    ->name('profile');

/* ------------------------------------------------------------------ */
/*  Admin panel                                                        */
/* ------------------------------------------------------------------ */
Route::middleware(['auth', 'verified', 'admin'])->prefix('admin')->name('admin.')->group(function () {
    Route::view('llm-models', 'admin.llm-models')->name('llm-models');
});

require __DIR__.'/auth.php';
