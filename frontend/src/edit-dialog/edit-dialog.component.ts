import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  selector: 'app-edit-dialog',
  templateUrl: './edit-dialog.component.html',
  styleUrls: ['./edit-dialog.component.css']
})
export class EditDialogComponent {
  constructor(@Inject(MAT_DIALOG_DATA) public element: any) {}

  saveChanges() {

  }
  cancelEdit() {
    
  }
}
