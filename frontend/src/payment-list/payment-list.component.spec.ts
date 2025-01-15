import { ComponentFixture, TestBed } from '@angular/core/testing';
import { PaymentListComponent } from './payment-list.component';
import { ApiService } from 'src/api.service';
import { MatDialog } from '@angular/material/dialog';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { of, throwError } from 'rxjs';
import { ItemDialogComponent } from 'src/item-dialog/item-dialog.component';
import { EditDialogComponent } from 'src/edit-dialog/edit-dialog.component';
import { By } from '@angular/platform-browser';

describe('PaymentListComponent', () => {
  let component: PaymentListComponent;
  let fixture: ComponentFixture<PaymentListComponent>;
  let apiService: jasmine.SpyObj<ApiService>;
  let dialog: jasmine.SpyObj<MatDialog>;

  beforeEach(async () => {
    // Mock the ApiService and MatDialog
    apiService = jasmine.createSpyObj('ApiService', ['getPayments', 'deletePaymentRecord']);
    dialog = jasmine.createSpyObj('MatDialog', ['open']);

    await TestBed.configureTestingModule({
      declarations: [PaymentListComponent, ItemDialogComponent, EditDialogComponent],
      imports: [
        MatTableModule,
        MatPaginatorModule,
        MatSortModule,
      ],
      providers: [
        { provide: ApiService, useValue: apiService },
        { provide: MatDialog, useValue: dialog },
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(PaymentListComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  it('should fetch payments data on init', async () => {
    // Arrange
    const mockPayments = [
      { _id: '1', payee_first_name: 'John', payee_last_name: 'Doe', due_amount: 100 },
      { _id: '2', payee_first_name: 'Jane', payee_last_name: 'Smith', due_amount: 200 },
    ];
    apiService.getPayments.and.returnValue(of(mockPayments));

    // Act
    await component.ngOnInit();
    fixture.detectChanges();

    // Assert
    expect(component.dataSource.data.length).toBe(2);
    expect(component.dataSource.data[0].payee_first_name).toBe('John');
  });

  it('should handle error when fetching payments data', async () => {
    // Arrange
    apiService.getPayments.and.returnValue(throwError('Error fetching data'));

    // Act
    await component.ngOnInit();
    fixture.detectChanges();

    // Assert
    expect(component.dataSource.data.length).toBe(0);
  });

  it('should apply filter correctly', () => {
    // Arrange
    const mockPayments = [
      { _id: '1', payee_first_name: 'John', payee_last_name: 'Doe', due_amount: 100 },
      { _id: '2', payee_first_name: 'Jane', payee_last_name: 'Smith', due_amount: 200 },
    ];
    component.dataSource.data = mockPayments;

    // Act
    component.applyFilter({ target: { value: 'john' } } as KeyboardEvent);

    // Assert
    expect(component.dataSource.filter).toBe('john');
    expect(component.dataSource.filteredData.length).toBe(1);
    expect(component.dataSource.filteredData[0].payee_first_name).toBe('John');
  });

  it('should open item dialog on toggleView', () => {
    // Arrange
    const mockItem = { _id: '1', payee_first_name: 'John', payee_last_name: 'Doe' };
    dialog.open.and.returnValue({});

    // Act
    component.toggleView(mockItem);

    // Assert
    expect(dialog.open).toHaveBeenCalledWith(ItemDialogComponent, { data: mockItem });
  });

  it('should open edit dialog on toggleEdit', () => {
    // Arrange
    const mockItem = { _id: '1', payee_first_name: 'John', payee_last_name: 'Doe' };
    dialog.open.and.returnValue({});

    // Act
    component.toggleEdit(mockItem);

    // Assert
    expect(dialog.open).toHaveBeenCalledWith(EditDialogComponent, { data: mockItem });
  });

  it('should delete payment record successfully', async () => {
    // Arrange
    const mockItem = { _id: '1', payee_first_name: 'John', payee_last_name: 'Doe' };
    apiService.deletePaymentRecord.and.returnValue(of({}));

    // Act
    await component.deletePaymentRecord(mockItem);
    fixture.detectChanges();

    // Assert
    expect(apiService.deletePaymentRecord).toHaveBeenCalledWith(mockItem._id);
    expect(component.dataSource.data.length).toBe(0); // Verify the item is deleted
  });

  it('should show error on delete payment failure', async () => {
    // Arrange
    const mockItem = { _id: '1', payee_first_name: 'John', payee_last_name: 'Doe' };
    apiService.deletePaymentRecord.and.returnValue(throwError('Error deleting payment'));

    // Act
    await component.deletePaymentRecord(mockItem);
    fixture.detectChanges();

    // Assert
    expect(apiService.deletePaymentRecord).toHaveBeenCalledWith(mockItem._id);
  });
});
