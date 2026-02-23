<div>
    {{-- Flash status --}}
    @if (session('status'))
        <div class="mb-4 rounded-md bg-green-900/40 border border-green-700 px-4 py-3 text-sm text-green-300">
            {{ session('status') }}
        </div>
    @endif

    {{-- Toolbar: search + add button --}}
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6">
        <input
            wire:model.live.debounce.300ms="search"
            type="text"
            placeholder="Search models…"
            class="w-full sm:w-72 rounded-md bg-mk-surface border border-mk-border text-mk-text placeholder-mk-muted px-3 py-2 text-sm focus:border-mk-fire focus:ring-mk-fire"
        />

        <button wire:click="openCreate" class="mk-btn-fire px-4 py-2 text-sm font-semibold rounded-md whitespace-nowrap">
            + Add Model
        </button>
    </div>

    {{-- Create / Edit slide-down form --}}
    @if ($showForm)
        <div class="mk-card p-6 mb-6 border border-mk-border rounded-lg shadow-lg">
            <h3 class="text-lg font-bold text-mk-text mb-4">
                {{ $editingId ? 'Edit Model' : 'New Model' }}
            </h3>

            <form wire:submit="save" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {{-- Name --}}
                <div>
                    <x-input-label for="name" value="Display Name" />
                    <x-text-input wire:model="name" id="name" class="mt-1 block w-full" required />
                    <x-input-error :messages="$errors->get('name')" class="mt-1" />
                </div>

                {{-- Slug (Ollama tag) --}}
                <div>
                    <x-input-label for="slug" value="Ollama Tag (slug)" />
                    <x-text-input wire:model="slug" id="slug" class="mt-1 block w-full" placeholder="e.g. llama3.2:3b" required />
                    <x-input-error :messages="$errors->get('slug')" class="mt-1" />
                </div>

                {{-- Parameter size --}}
                <div>
                    <x-input-label for="parameterSize" value="Parameter Size" />
                    <x-text-input wire:model="parameterSize" id="parameterSize" class="mt-1 block w-full" placeholder="e.g. 12b" />
                    <x-input-error :messages="$errors->get('parameterSize')" class="mt-1" />
                </div>

                {{-- Provider --}}
                <div>
                    <x-input-label for="provider" value="Provider" />
                    <x-text-input wire:model="provider" id="provider" class="mt-1 block w-full" />
                    <x-input-error :messages="$errors->get('provider')" class="mt-1" />
                </div>

                {{-- Description (full width) --}}
                <div class="sm:col-span-2">
                    <x-input-label for="description" value="Description" />
                    <textarea
                        wire:model="description"
                        id="description"
                        rows="2"
                        class="mt-1 block w-full rounded-md bg-mk-surface border border-mk-border text-mk-text placeholder-mk-muted focus:border-mk-fire focus:ring-mk-fire"
                    ></textarea>
                    <x-input-error :messages="$errors->get('description')" class="mt-1" />
                </div>

                {{-- Active toggle --}}
                <div class="sm:col-span-2 flex items-center gap-2">
                    <input wire:model="isActive" id="isActive" type="checkbox"
                           class="rounded border-mk-border bg-mk-surface text-mk-fire focus:ring-mk-fire" />
                    <x-input-label for="isActive" value="Active" />
                </div>

                {{-- Buttons --}}
                <div class="sm:col-span-2 flex items-center gap-3 pt-2">
                    <x-primary-button type="submit">
                        {{ $editingId ? 'Update' : 'Create' }}
                    </x-primary-button>
                    <x-secondary-button type="button" wire:click="$set('showForm', false)">
                        Cancel
                    </x-secondary-button>
                </div>
            </form>
        </div>
    @endif

    {{-- Models table --}}
    <div class="mk-card rounded-lg border border-mk-border overflow-hidden shadow">
        <table class="min-w-full divide-y divide-mk-border text-sm">
            <thead class="bg-mk-surface">
                <tr>
                    <th class="px-4 py-3 text-left font-semibold text-mk-muted uppercase tracking-wider">Name</th>
                    <th class="px-4 py-3 text-left font-semibold text-mk-muted uppercase tracking-wider">Slug</th>
                    <th class="px-4 py-3 text-left font-semibold text-mk-muted uppercase tracking-wider hidden sm:table-cell">Size</th>
                    <th class="px-4 py-3 text-left font-semibold text-mk-muted uppercase tracking-wider hidden md:table-cell">Provider</th>
                    <th class="px-4 py-3 text-center font-semibold text-mk-muted uppercase tracking-wider">Active</th>
                    <th class="px-4 py-3 text-right font-semibold text-mk-muted uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-mk-border bg-mk-card">
                @forelse ($models as $model)
                    <tr class="hover:bg-mk-surface/60 transition">
                        <td class="px-4 py-3 text-mk-text font-medium">{{ $model->name }}</td>
                        <td class="px-4 py-3 text-mk-muted font-mono text-xs">{{ $model->slug }}</td>
                        <td class="px-4 py-3 text-mk-muted hidden sm:table-cell">{{ $model->parameter_size ?? '—' }}</td>
                        <td class="px-4 py-3 text-mk-muted hidden md:table-cell">{{ $model->provider }}</td>
                        <td class="px-4 py-3 text-center">
                            <button wire:click="toggleActive({{ $model->id }})" title="Toggle active">
                                @if ($model->is_active)
                                    <span class="inline-block w-3 h-3 rounded-full bg-green-500"></span>
                                @else
                                    <span class="inline-block w-3 h-3 rounded-full bg-mk-muted"></span>
                                @endif
                            </button>
                        </td>
                        <td class="px-4 py-3 text-right space-x-2 whitespace-nowrap">
                            <button wire:click="openEdit({{ $model->id }})"
                                    class="text-mk-fire hover:text-mk-fire-light text-xs font-semibold uppercase tracking-wide">
                                Edit
                            </button>
                            <button wire:click="confirmDelete({{ $model->id }})"
                                    class="text-red-500 hover:text-red-400 text-xs font-semibold uppercase tracking-wide">
                                Delete
                            </button>
                        </td>
                    </tr>
                @empty
                    <tr>
                        <td colspan="6" class="px-4 py-8 text-center text-mk-muted">
                            No models found.
                        </td>
                    </tr>
                @endforelse
            </tbody>
        </table>

        @if ($models->hasPages())
            <div class="px-4 py-3 border-t border-mk-border bg-mk-surface">
                {{ $models->links() }}
            </div>
        @endif
    </div>

    {{-- Delete confirmation modal --}}
    @if ($confirmingDelete)
        <x-modal name="confirm-delete" :show="true">
            <div class="p-6">
                <h3 class="text-lg font-bold text-mk-text">Delete Model</h3>
                <p class="mt-2 text-sm text-mk-muted">
                    Are you sure you want to delete this model? This action cannot be undone.
                </p>

                <div class="mt-6 flex justify-end gap-3">
                    <x-secondary-button wire:click="cancelDelete">
                        Cancel
                    </x-secondary-button>
                    <x-danger-button wire:click="delete">
                        Delete
                    </x-danger-button>
                </div>
            </div>
        </x-modal>
    @endif
</div>
