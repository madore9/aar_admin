class PendingChanges {
    constructor(planId, requirementId) {
        this.planId = planId;
        this.requirementId = requirementId;
        this.key = `${planId}|${requirementId}`;
        this.additions = {};
        this.removals = [];
        this.modifications = {};
        this._load();
    }

    _load() {
        const saved = sessionStorage.getItem(`draft_${this.key}`);
        if (saved) {
            const d = JSON.parse(saved);
            this.additions = d.additions || {};
            this.removals = d.removals || [];
            this.modifications = d.modifications || {};
        }
    }

    _save() {
        sessionStorage.setItem(`draft_${this.key}`, JSON.stringify({
            additions: this.additions,
            removals: this.removals,
            modifications: this.modifications
        }));
        this._updateUI();
    }

    addCourse(identifier, courseData) {
        const idx = this.removals.indexOf(identifier);
        if (idx !== -1) {
            this.removals.splice(idx, 1);
        } else {
            this.additions[identifier] = courseData;
        }
        this._save();
    }

    removeCourse(identifier) {
        if (this.additions[identifier]) {
            delete this.additions[identifier];
        } else {
            if (!this.removals.includes(identifier)) {
                this.removals.push(identifier);
            }
        }
        this._save();
    }

    modifyCourse(identifier, changes) {
        this.modifications[identifier] = {
            ...(this.modifications[identifier] || {}),
            ...changes
        };
        this._save();
    }

    hasChanges() {
        return Object.keys(this.additions).length > 0 ||
               this.removals.length > 0 ||
               Object.keys(this.modifications).length > 0;
    }

    toJSON() {
        return {
            additions: this.additions,
            removals: this.removals,
            modifications: this.modifications
        };
    }

    clear() {
        this.additions = {};
        this.removals = [];
        this.modifications = {};
        sessionStorage.removeItem(`draft_${this.key}`);
        this._updateUI();
    }

    _updateUI() {
        // Toggle changes footer visibility
        const footer = document.querySelector(`[data-changes-footer="${this.key}"]`);
        if (footer) {
            footer.classList.toggle('hidden', !this.hasChanges());
        }

        // Update row visual states
        const section = document.querySelector(`[data-req-section="${this.requirementId}"]`);
        if (!section) return;

        section.querySelectorAll('[data-identifier]').forEach(row => {
            const id = row.dataset.identifier;
            const isRemoved = this.removals.includes(id);
            const isAdded = !!this.additions[id];

            row.classList.toggle('bg-red-50', isRemoved);
            row.classList.toggle('opacity-60', isRemoved);
            row.classList.toggle('line-through', isRemoved);
            row.classList.toggle('bg-green-50', isAdded);
        });
    }
}
